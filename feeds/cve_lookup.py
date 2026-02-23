"""CVE lookup integration with cve-search MongoDB database."""

import logging
from functools import lru_cache
from typing import Optional, Dict, List

try:
    import pymongo
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

from django.conf import settings


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_cve_db_connection():
    """
    Get connection to cve-search MongoDB database.

    Returns:
        MongoDB database object or None if unavailable
    """
    if not PYMONGO_AVAILABLE:
        logger.warning("pymongo not installed - CVE lookup unavailable")
        return None

    try:
        client = pymongo.MongoClient(
            settings.CVE_SEARCH_MONGO_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
        )
        # Test connection
        client.server_info()
        db = client[settings.CVE_SEARCH_DB_NAME]
        logger.info(f"Connected to cve-search database: {settings.CVE_SEARCH_DB_NAME}")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to cve-search MongoDB: {e}")
        return None


def lookup_cve(cve_id: str) -> Optional[Dict]:
    """
    Query cve-search for CVE details.

    Args:
        cve_id: CVE identifier (e.g., "CVE-2021-44228")

    Returns:
        Dict with CVE details or None if not found
        {
            'id': str,
            'summary': str,
            'cvss': float,
            'cvss_v3': float,
            'severity': str,
            'published': datetime,
            'modified': datetime,
            'references': List[str],
            'vulnerable_products': List[str],
        }
    """
    db = get_cve_db_connection()
    if not db:
        return None

    try:
        # Query the cves collection
        cve_doc = db.cves.find_one({"id": cve_id.upper()})

        if not cve_doc:
            logger.debug(f"CVE not found in database: {cve_id}")
            return None

        # Extract and normalize fields
        result = {
            "id": cve_doc.get("id", cve_id),
            "summary": cve_doc.get("summary", ""),
        }

        # CVSS scores
        if "cvss" in cve_doc:
            result["cvss"] = float(cve_doc["cvss"])
        elif "impact" in cve_doc and "baseMetricV2" in cve_doc["impact"]:
            result["cvss"] = float(
                cve_doc["impact"]["baseMetricV2"].get("cvssV2", {}).get("baseScore", 0)
            )

        if "cvss-vector" in cve_doc:
            result["cvss_vector"] = cve_doc["cvss-vector"]

        # CVSS v3
        if "impact" in cve_doc and "baseMetricV3" in cve_doc["impact"]:
            result["cvss_v3"] = float(
                cve_doc["impact"]["baseMetricV3"].get("cvssV3", {}).get("baseScore", 0)
            )

        # Severity (calculate from CVSS if not present)
        if "severity" in cve_doc:
            result["severity"] = cve_doc["severity"]
        else:
            cvss_score = result.get("cvss_v3") or result.get("cvss", 0)
            if cvss_score >= 9.0:
                result["severity"] = "CRITICAL"
            elif cvss_score >= 7.0:
                result["severity"] = "HIGH"
            elif cvss_score >= 4.0:
                result["severity"] = "MEDIUM"
            elif cvss_score > 0:
                result["severity"] = "LOW"
            else:
                result["severity"] = "UNKNOWN"

        # Dates
        if "Published" in cve_doc:
            result["published"] = cve_doc["Published"]
        if "Modified" in cve_doc:
            result["modified"] = cve_doc["Modified"]
        if "last-modified" in cve_doc:
            result["last_modified"] = cve_doc["last-modified"]

        # References
        references = []
        if "references" in cve_doc:
            for ref in cve_doc["references"]:
                if isinstance(ref, str):
                    references.append(ref)
                elif isinstance(ref, dict) and "url" in ref:
                    references.append(ref["url"])
        result["references"] = references

        # Vulnerable products/configurations
        vulnerable_products = []
        if "vulnerable_product" in cve_doc:
            vulnerable_products = cve_doc["vulnerable_product"]
        elif "vulnerable_configuration" in cve_doc:
            vulnerable_products = cve_doc["vulnerable_configuration"]
        result["vulnerable_products"] = vulnerable_products[:20]  # Limit to first 20

        # CWE
        if "cwe" in cve_doc:
            result["cwe"] = cve_doc["cwe"]

        return result

    except Exception as e:
        logger.error(f"Error looking up CVE {cve_id}: {e}")
        return None


def bulk_lookup_cves(cve_ids: List[str]) -> Dict[str, Dict]:
    """
    Efficiently lookup multiple CVEs in a single query.

    Args:
        cve_ids: List of CVE identifiers

    Returns:
        Dict mapping CVE ID to CVE details
    """
    db = get_cve_db_connection()
    if not db or not cve_ids:
        return {}

    try:
        # Normalize CVE IDs
        normalized_ids = [cve_id.upper() for cve_id in cve_ids]

        # Query all CVEs at once
        cve_docs = db.cves.find({"id": {"$in": normalized_ids}})

        results = {}
        for doc in cve_docs:
            cve_id = doc.get("id")
            if cve_id:
                # Reuse single lookup logic
                results[cve_id] = lookup_cve(cve_id)

        return results

    except Exception as e:
        logger.error(f"Error bulk looking up CVEs: {e}")
        return {}


def test_connection() -> bool:
    """
    Test connection to cve-search database.

    Returns:
        True if connection successful, False otherwise
    """
    db = get_cve_db_connection()
    if not db:
        return False

    try:
        # Try to count documents in cves collection
        count = db.cves.count_documents({})
        logger.info(f"cve-search database has {count:,} CVE entries")
        return True
    except Exception as e:
        logger.error(f"Failed to query cve-search database: {e}")
        return False

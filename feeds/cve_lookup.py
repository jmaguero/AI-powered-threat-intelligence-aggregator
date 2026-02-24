"""CVE lookup integration with cve-search public API (cve.circl.lu)."""

import logging
import time
from typing import Optional, Dict, List

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_api_base_url() -> str:
    """Get the base URL for the cve-search API."""
    base_url = getattr(settings, "CVE_SEARCH_API_BASE_URL", "https://cve.circl.lu/api/")
    if not base_url.endswith("/"):
        base_url += "/"
    return base_url


def lookup_cve(cve_id: str) -> Optional[Dict]:
    """
    Query cve.circl.lu API for CVE details, utilizing Redis cache.

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
            'published': str,
            'modified': str,
            'references': List[str],
            'vulnerable_products': List[str],
        }
    """
    if not cve_id:
        return None

    cve_id = cve_id.upper()
    cache_key = f"cve_lookup_{cve_id}"

    # 1. Check cache first
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data

    # 2. Fetch from API if not in cache
    api_url = f"{get_api_base_url()}cve/{cve_id}"

    try:
        response = requests.get(api_url, timeout=10)

        if response.status_code == 404:
            logger.debug(f"CVE not found in CIRCL API: {cve_id}")
            # Cache the "not found" state briefly to avoid hammering the API for invalid CVEs
            cache.set(cache_key, None, timeout=3600)  # 1 hour
            return None

        response.raise_for_status()
        cve_doc = response.json()

        if not cve_doc:
            return None

        # 3. Extract and normalize fields to match existing schema
        result = _normalize_cve_data(cve_doc, cve_id)

        # 4. Store in cache
        cache_timeout = getattr(settings, "CVE_CACHE_TIMEOUT", 86400)  # Default 24h
        cache.set(cache_key, result, timeout=cache_timeout)

        return result

    except requests.exceptions.Timeout:
        logger.error(f"Timeout querying cve.circl.lu for {cve_id}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error querying cve.circl.lu for {cve_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing CVE {cve_id}: {e}")
        return None


def _normalize_cve_data(cve_doc: Dict, cve_id: str) -> Dict:
    """Helper to normalize the CIRCL API JSON 5.1 doc into our standard format."""

    result = {
        "id": cve_id,
        "summary": "",
        "cvss": 0.0,
        "cvss_v3": 0.0,
        "cvss_vector": "",
        "severity": "UNKNOWN",
        "published": "",
        "modified": "",
        "references": [],
        "vulnerable_products": [],
        "cwe": "",
    }

    # Meta data dates
    meta = cve_doc.get("cveMetadata", {})
    result["published"] = meta.get("datePublished", "")
    result["modified"] = meta.get("dateUpdated", "")
    result["last_modified"] = meta.get("dateUpdated", "")

    containers = cve_doc.get("containers", {})
    cna = containers.get("cna", {})
    adps = containers.get("adp", [])

    # Summary
    descriptions = cna.get("descriptions", [])
    if descriptions:
        # Try to find English desc
        en_desc = next(
            (d.get("value") for d in descriptions if d.get("lang") == "en"), None
        )
        result["summary"] = en_desc or descriptions[0].get("value", "")

    # References
    for ref in cna.get("references", []):
        url = ref.get("url")
        if url:
            result["references"].append(url)

    # Metrics (CVSS)
    metrics_list = cna.get("metrics", [])
    for adp in adps:
        metrics_list.extend(adp.get("metrics", []))

    cvss_v2, cvss_v3 = 0.0, 0.0
    cvss_vector, severity = "", ""

    for m in metrics_list:
        if "cvssV3_1" in m or "cvssV3_0" in m:
            v3 = m.get("cvssV3_1") or m.get("cvssV3_0")
            score = float(v3.get("baseScore", 0))
            if score > cvss_v3:
                cvss_v3 = score
                cvss_vector = v3.get("vectorString", cvss_vector)
                severity = v3.get("baseSeverity", severity)
        elif "cvssV2_0" in m:
            v2 = m.get("cvssV2_0")
            score = float(v2.get("baseScore", 0))
            if score > cvss_v2:
                cvss_v2 = score
                if (
                    not cvss_vector
                ):  # V3 takes precedence for vector and severity if available later
                    cvss_vector = v2.get("vectorString", "")
                    # V2 didn't always have baseSeverity, we'll calculate it if missing

    result["cvss"] = cvss_v2
    result["cvss_v3"] = cvss_v3
    result["cvss_vector"] = cvss_vector

    # Severity
    if severity:
        result["severity"] = str(severity).upper()
    else:
        # Calculate if not explicitly provided
        score = cvss_v3 or cvss_v2
        if score >= 9.0:
            result["severity"] = "CRITICAL"
        elif score >= 7.0:
            result["severity"] = "HIGH"
        elif score >= 4.0:
            result["severity"] = "MEDIUM"
        elif score > 0:
            result["severity"] = "LOW"

    # CWE
    problem_types = cna.get("problemTypes", [])
    for pt in problem_types:
        for desc in pt.get("descriptions", []):
            if desc.get("cweId"):
                result["cwe"] = desc.get("cweId")
                break
            elif "CWE" in desc.get("description", ""):
                result["cwe"] = desc.get("description")
                break
        if result["cwe"]:
            break

    # Affected products (simplified extraction for JSON 5.1)
    affected = cna.get("affected", [])
    for aff in affected:
        vendor = aff.get("vendor", "Unknown")
        product = aff.get("product", "Unknown")
        # Format something readable since CPEs are complex in 5.1
        if vendor != "Unknown" and product != "Unknown":
            result["vulnerable_products"].append(f"{vendor}:{product}")
        elif product != "Unknown":
            result["vulnerable_products"].append(product)

    return result


def bulk_lookup_cves(cve_ids: List[str]) -> Dict[str, Dict]:
    """
    Lookup multiple CVEs, utilizing cache and staggering API requests.

    Args:
        cve_ids: List of CVE identifiers

    Returns:
        Dict mapping CVE ID to CVE details
    """
    if not cve_ids:
        return {}

    results = {}
    normalized_ids = [cve_id.upper() for cve_id in cve_ids]

    # Process sequentially to respect rate limits
    for i, cve_id in enumerate(normalized_ids):
        # The inner method handles caching
        cve_data = lookup_cve(cve_id)
        if cve_data:
            results[cve_id] = cve_data

        # Add a small delay between requests to not overwhelm the API
        # Only sleep if we suspect an API call was made (not instantly from cache)
        # 0.1s ensures max 10 requests per second
        if i < len(normalized_ids) - 1:
            time.sleep(0.1)

    return results


def test_connection() -> bool:
    """
    Test connection to cve.circl.lu public API.

    Returns:
        True if connection successful, False otherwise
    """
    api_url = f"{get_api_base_url()}dbInfo"
    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Connected to cve.circl.lu API. DB Info: {data}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to cve.circl.lu API: {e}")
        return False

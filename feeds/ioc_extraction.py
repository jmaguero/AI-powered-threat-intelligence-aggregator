"""IOC (Indicator of Compromise) extraction from threat intelligence text."""

import re
import ipaddress
from typing import List, Dict, Optional


# Regex patterns for IOC extraction
PATTERNS = {
    "ip": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    ),
    "domain": re.compile(
        r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b"
    ),
    "url": re.compile(
        r"https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?"
    ),
    "md5": re.compile(r"\b[a-fA-F0-9]{32}\b"),
    "sha1": re.compile(r"\b[a-fA-F0-9]{40}\b"),
    "sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
    "cve": re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE),
    "email": re.compile(
        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
    ),
}

# Defanged patterns to normalize obfuscated IOCs
DEFANG_PATTERNS = [
    (r"\[\.?\]", "."),  # 192[.]168[.]1[.]1 -> 192.168.1.1
    (r"\(\.\)", "."),  # 192(.)168(.)1(.)1 -> 192.168.1.1
    (r"hxxp", "http"),  # hxxp://evil.com -> http://evil.com
    (r"hXXp", "http"),  # hXXp://evil.com -> http://evil.com
    (r"\[@\]", "@"),  # user[@]domain.com -> user@domain.com
    (r"\(@\)", "@"),  # user(@)domain.com -> user@domain.com
]

# False positive filters
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
]

DOMAIN_BLOCKLIST = {
    "example.com",
    "example.org",
    "example.net",
    "localhost",
    "test.com",
    "domain.com",
    "email.com",
    "mail.com",
}


def refang_text(text: str) -> str:
    """
    Normalize defanged/obfuscated IOCs to their original form.

    Examples:
        192[.]168[.]1[.]1 -> 192.168.1.1
        hxxps://evil[.]com -> https://evil.com
    """
    refanged = text
    for pattern, replacement in DEFANG_PATTERNS:
        refanged = re.sub(pattern, replacement, refanged, flags=re.IGNORECASE)
    return refanged


def is_valid_ip(ip_str: str) -> bool:
    """Validate IP address and exclude private/reserved ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)

        # Exclude private and reserved ranges
        for network in PRIVATE_IP_RANGES:
            if ip in network:
                return False

        # Exclude multicast and reserved
        if ip.is_multicast or ip.is_reserved:
            return False

        return True
    except ValueError:
        return False


def is_valid_domain(domain: str) -> bool:
    """Validate domain and exclude common false positives."""
    domain = domain.lower().strip()

    # Exclude blocklisted domains
    if domain in DOMAIN_BLOCKLIST:
        return False

    # Must have at least one dot
    if "." not in domain:
        return False

    # Exclude domains that are too short (likely fragments)
    if len(domain) < 4:
        return False

    # Exclude IP addresses caught by domain pattern
    if PATTERNS["ip"].match(domain):
        return False

    return True


def is_valid_hash(hash_str: str, hash_type: str) -> bool:
    """Validate hash format and length."""
    hash_str = hash_str.lower()

    expected_lengths = {
        "md5": 32,
        "sha1": 40,
        "sha256": 64,
    }

    if hash_type not in expected_lengths:
        return False

    # Check length
    if len(hash_str) != expected_lengths[hash_type]:
        return False

    # Check if all hex
    if not re.match(r"^[a-f0-9]+$", hash_str):
        return False

    return True


def is_valid_cve(cve_id: str) -> bool:
    """Validate CVE ID format and year range."""
    cve_id = cve_id.upper()

    # Must match CVE format
    match = re.match(r"^CVE-(\d{4})-(\d{4,7})$", cve_id)
    if not match:
        return False

    year = int(match.group(1))

    # CVE program started in 1999, allow up to current year + 1
    if year < 1999 or year > 2027:
        return False

    return True


def extract_context(text: str, match_pos: int, context_size: int = 100) -> str:
    """Extract surrounding context around a match."""
    start = max(0, match_pos - context_size)
    end = min(len(text), match_pos + context_size)
    return text[start:end].strip()


def extract_iocs_from_text(
    text: str, article_id: Optional[int] = None
) -> List[Dict[str, str]]:
    """
    Extract IOCs from text using regex patterns.

    Args:
        text: Text to extract IOCs from
        article_id: Optional article ID for logging

    Returns:
        List of dicts with keys: value, type, confidence, context
    """
    if not text or len(text.strip()) < 10:
        return []

    # Refang obfuscated IOCs first
    refanged_text = refang_text(text)

    extracted_iocs = []
    seen = set()  # Track unique (type, value) pairs to avoid duplicates

    # Extract CVEs (case-insensitive, high confidence)
    for match in PATTERNS["cve"].finditer(refanged_text):
        cve_id = match.group(0).upper()
        if is_valid_cve(cve_id):
            key = ("cve", cve_id)
            if key not in seen:
                seen.add(key)
                extracted_iocs.append({
                    "value": cve_id,
                    "type": "cve",
                    "confidence": "high",
                    "context": extract_context(refanged_text, match.start()),
                })

    # Extract IPs
    for match in PATTERNS["ip"].finditer(refanged_text):
        ip = match.group(0)
        if is_valid_ip(ip):
            key = ("ip", ip)
            if key not in seen:
                seen.add(key)
                extracted_iocs.append({
                    "value": ip,
                    "type": "ip",
                    "confidence": "high",
                    "context": extract_context(refanged_text, match.start()),
                })

    # Extract domains (exclude URLs to avoid duplicates)
    for match in PATTERNS["domain"].finditer(refanged_text):
        domain = match.group(0).lower()

        # Skip if this is part of a URL or email
        start_pos = match.start()
        if start_pos > 0 and refanged_text[start_pos - 1] in ("@", "/", ":"):
            continue

        if is_valid_domain(domain):
            key = ("domain", domain)
            if key not in seen:
                seen.add(key)
                extracted_iocs.append({
                    "value": domain,
                    "type": "domain",
                    "confidence": "high",
                    "context": extract_context(refanged_text, match.start()),
                })

    # Extract URLs
    for match in PATTERNS["url"].finditer(refanged_text):
        url = match.group(0)
        key = ("url", url)
        if key not in seen:
            seen.add(key)
            extracted_iocs.append({
                "value": url,
                "type": "url",
                "confidence": "high",
                "context": extract_context(refanged_text, match.start()),
            })

    # Extract hashes (MD5, SHA1, SHA256)
    for hash_type in ["sha256", "sha1", "md5"]:
        for match in PATTERNS[hash_type].finditer(refanged_text):
            hash_value = match.group(0).lower()
            if is_valid_hash(hash_value, hash_type):
                key = (hash_type, hash_value)
                if key not in seen:
                    seen.add(key)
                    extracted_iocs.append({
                        "value": hash_value,
                        "type": hash_type,
                        "confidence": "high",
                        "context": extract_context(refanged_text, match.start()),
                    })

    # Extract emails
    for match in PATTERNS["email"].finditer(refanged_text):
        email = match.group(0).lower()
        # Exclude common false positives
        if not any(fp in email for fp in ["example", "test", "domain"]):
            key = ("email", email)
            if key not in seen:
                seen.add(key)
                extracted_iocs.append({
                    "value": email,
                    "type": "email",
                    "confidence": "medium",  # Emails are less reliable
                    "context": extract_context(refanged_text, match.start()),
                })

    return extracted_iocs

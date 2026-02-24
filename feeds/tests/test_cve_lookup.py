"""Tests for CVE lookup integration."""

import requests
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from feeds.cve_lookup import (
    lookup_cve,
    bulk_lookup_cves,
    _normalize_cve_data,
)


class TestCVELookup(TestCase):
    def setUp(self):
        """Clear the Django cache before each test."""
        cache.clear()

    def tearDown(self):
        cache.clear()

    @property
    def mock_cve_json_51_payload(self):
        """Returns a mock JSON 5.1 payload similar to what cve.circl.lu returns."""
        return {
            "dataType": "CVE_RECORD",
            "dataVersion": "5.1",
            "cveMetadata": {
                "cveId": "CVE-2021-44228",
                "datePublished": "2021-12-10T00:00:00.000Z",
                "dateUpdated": "2025-10-21T23:25:23.121Z",
            },
            "containers": {
                "cna": {
                    "descriptions": [
                        {
                            "lang": "en",
                            "value": "Apache Log4j2 JNDI features do not protect against attacker controlled LDAP...",
                        }
                    ],
                    "affected": [
                        {
                            "vendor": "Apache Software Foundation",
                            "product": "Apache Log4j2",
                        }
                    ],
                    "problemTypes": [
                        {
                            "descriptions": [
                                {
                                    "cweId": "CWE-502",
                                    "description": "Deserialization of Untrusted Data",
                                }
                            ]
                        }
                    ],
                    "references": [
                        {"url": "https://logging.apache.org/log4j/2.x/security.html"}
                    ],
                },
                "adp": [
                    {
                        "metrics": [
                            {
                                "cvssV3_1": {
                                    "baseScore": 10.0,
                                    "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
                                    "baseSeverity": "CRITICAL",
                                }
                            }
                        ]
                    }
                ],
            },
        }

    @patch("feeds.cve_lookup.requests.get")
    def test_lookup_cve_success(self, mock_get):
        """Test successful lookup of a CVE using the CIRCL API format."""
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_cve_json_51_payload

        result = lookup_cve("CVE-2021-44228")

        mock_get.assert_called_once_with(
            "https://cve.circl.lu/api/cve/CVE-2021-44228", timeout=10
        )

        # Verify JSON 5.1 normalization
        assert result is not None
        assert result["id"] == "CVE-2021-44228"
        assert result["summary"].startswith("Apache Log4j2 JNDI")
        assert result["cvss_v3"] == 10.0
        assert result["severity"] == "CRITICAL"
        assert result["vulnerable_products"] == [
            "Apache Software Foundation:Apache Log4j2"
        ]
        assert result["cwe"] == "CWE-502"

        # Verify cache was populated
        cached_val = cache.get("cve_lookup_CVE-2021-44228")
        assert cached_val is not None
        assert cached_val["id"] == "CVE-2021-44228"

    @patch("feeds.cve_lookup.requests.get")
    def test_lookup_cve_not_found(self, mock_get):
        """Test looking up a CVE that does not exist."""
        mock_response = mock_get.return_value
        mock_response.status_code = 404

        result = lookup_cve("CVE-INVALID")

        assert result is None

        # Verify that we cached the None result so we don't hammer the API
        assert cache.has_key("cve_lookup_CVE-INVALID")
        assert cache.get("cve_lookup_CVE-INVALID") is None

    @patch("feeds.cve_lookup.requests.get")
    def test_lookup_cve_timeout(self, mock_get):
        """Test graceful degradation if the API times out."""
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        result = lookup_cve("CVE-2021-44228")

        assert result is None

        # We don't cache true timeouts (it might be a transient network issue)
        assert not cache.has_key("cve_lookup_CVE-2021-44228")

    @patch("feeds.cve_lookup.requests.get")
    def test_lookup_cve_cache_hit(self, mock_get):
        """Test that requests are bypassed if the cache holds the data."""
        # Pre-populate cache
        mock_entry = {"id": "CVE-CACHE", "severity": "HIGH"}
        cache.set("cve_lookup_CVE-CACHE", mock_entry, 60)

        result = lookup_cve("CVE-CACHE")

        assert result == mock_entry
        mock_get.assert_not_called()

    def test_normalize_no_metrics(self):
        """Test normalization when no CVSS metrics are provided."""
        payload = {
            "dataType": "CVE_RECORD",
            "containers": {
                "cna": {"descriptions": [{"value": "A bad bug", "lang": "en"}]}
            },
        }

        result = _normalize_cve_data(payload, "CVE-NO-METRICS")

        assert result["cvss"] == 0.0
        assert result["cvss_v3"] == 0.0
        assert result["severity"] == "UNKNOWN"

    def test_normalize_v2_v3_precedence(self):
        """Test that V3 metrics override V2 if both are present."""
        payload = {
            "dataType": "CVE_RECORD",
            "containers": {
                "cna": {
                    "metrics": [
                        {"cvssV2_0": {"baseScore": 5.0, "vectorString": "AV:N/AC:L"}},
                        {
                            "cvssV3_1": {
                                "baseScore": 8.0,
                                "vectorString": "CVSS:3.1/AV:N",
                                "baseSeverity": "HIGH",
                            }
                        },
                    ]
                }
            },
        }

        result = _normalize_cve_data(payload, "CVE-MIXED")

        assert result["cvss"] == 5.0  # Preserved V2 score
        assert result["cvss_v3"] == 8.0  # Extracted V3 score
        assert result["severity"] == "HIGH"  # V3 severity applies

    @patch("feeds.cve_lookup.time.sleep")
    @patch("feeds.cve_lookup.lookup_cve")
    def test_bulk_lookup_throttling(self, mock_lookup, mock_sleep):
        """Test that bulk lookups introduce delays between external queries."""
        mock_lookup.side_effect = [{"id": "CVE-1"}, {"id": "CVE-2"}, {"id": "CVE-3"}]

        cve_list = ["CVE-1", "CVE-2", "CVE-3"]

        results = bulk_lookup_cves(cve_list)

        assert len(results) == 3
        # Should call lookup_cve 3 times
        assert mock_lookup.call_count == 3
        # Should sleep exactly twice (between 1-2 and 2-3)
        assert mock_sleep.call_count == 2

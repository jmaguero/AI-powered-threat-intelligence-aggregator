from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
import re

from feeds.models import Article, IOC
from feeds.serializers import ArticleSerializer, IOCSerializer, CVEDetailSerializer
from feeds.filters import ArticleFilter, IOCFilter
from feeds.cve_lookup import lookup_cve


class ArticleListView(ListAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ArticleFilter


class ArticleDetailView(RetrieveAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer


class IOCListView(ListAPIView):
    """
    List IOCs with filtering capabilities.

    Query parameters:
        ioc_type: Filter by IOC type (ip, domain, url, md5, sha1, sha256, cve, email)
        value: Filter by value (partial match)
        confidence: Filter by confidence level (high, medium, low)
        first_seen_after: Filter by first seen date (ISO format)
        first_seen_before: Filter by first seen before date (ISO format)
        min_times_seen: Minimum number of times seen
        is_validated: Filter validated IOCs (true/false)
        is_false_positive: Filter false positives (true/false)
    """
    queryset = IOC.objects.all()
    serializer_class = IOCSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IOCFilter


class IOCDetailView(RetrieveAPIView):
    """
    Get details of a specific IOC including related articles.
    """
    queryset = IOC.objects.all()
    serializer_class = IOCSerializer


@api_view(['GET'])
def cve_detail_view(request, cve_id):
    """
    Get detailed information about a CVE from cve-search database.

    Path parameter:
        cve_id: CVE identifier (e.g., CVE-2021-44228)

    Returns:
        CVE details including CVSS scores, severity, references, and vulnerable products.
        Also includes our tracking data if this CVE has been seen in our feeds.
    """
    # Validate CVE ID format
    if not re.match(r'^CVE-\d{4}-\d{4,7}$', cve_id, re.IGNORECASE):
        return Response(
            {"error": "Invalid CVE ID format. Expected: CVE-YYYY-NNNN"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Normalize CVE ID to uppercase
    cve_id = cve_id.upper()

    # Lookup CVE in cve-search database
    cve_data = lookup_cve(cve_id)

    if not cve_data:
        return Response(
            {"error": f"CVE {cve_id} not found in database"},
            status=status.HTTP_404_NOT_FOUND
        )

    # Add our tracking data if this CVE is in our IOC database
    try:
        ioc = IOC.objects.filter(ioc_type='cve', value=cve_id).first()
        if ioc:
            cve_data['seen_in_articles'] = list(ioc.articles.values_list('id', flat=True))
            cve_data['first_seen_in_feed'] = ioc.first_seen
            cve_data['times_seen'] = ioc.times_seen
    except Exception:
        # Don't fail the request if tracking data lookup fails
        pass

    # Serialize and return
    serializer = CVEDetailSerializer(cve_data)
    return Response(serializer.data)

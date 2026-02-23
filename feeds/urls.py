from django.urls import path

from feeds.views import (
    ArticleListView,
    ArticleDetailView,
    IOCListView,
    IOCDetailView,
    cve_detail_view,
)

urlpatterns = [
    path("", ArticleListView.as_view(), name="article-list"),
    path("<int:pk>/", ArticleDetailView.as_view(), name="article-detail"),
    # IOC endpoints
    path("iocs/", IOCListView.as_view(), name="ioc-list"),
    path("iocs/<int:pk>/", IOCDetailView.as_view(), name="ioc-detail"),
    # CVE endpoints
    path("cves/<str:cve_id>/", cve_detail_view, name="cve-detail"),
]

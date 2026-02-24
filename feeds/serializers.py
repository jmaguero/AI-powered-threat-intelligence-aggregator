from rest_framework import serializers

from feeds.models import Article, IOC


class ArticleSerializer(serializers.ModelSerializer):
    ioc_count = serializers.SerializerMethodField()
    iocs = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "published_date",
            "link",
            "summary",
            "source",
            "created_at",
            "ai_summary",
            "threat_type",
            "severity",
            "affected_tech",
            "enriched_at",
            "ioc_count",
            "iocs",
        ]

    def get_ioc_count(self, obj):
        return obj.iocs.count()

    def get_iocs(self, obj):
        from feeds.serializers import IOCSerializer

        return IOCSerializer(obj.iocs.all(), many=True).data


class IOCSerializer(serializers.ModelSerializer):
    article_count = serializers.SerializerMethodField()
    article_ids = serializers.SerializerMethodField()

    class Meta:
        model = IOC
        fields = [
            "id",
            "value",
            "ioc_type",
            "confidence",
            "context",
            "first_seen",
            "last_seen",
            "times_seen",
            "is_validated",
            "is_false_positive",
            "article_count",
            "article_ids",
        ]

    def get_article_count(self, obj):
        return obj.articles.count()

    def get_article_ids(self, obj):
        return list(obj.articles.values_list("id", flat=True))


class CVEDetailSerializer(serializers.Serializer):
    """Serializer for CVE data from cve-search database."""

    id = serializers.CharField()
    summary = serializers.CharField()
    cvss = serializers.FloatField(required=False)
    cvss_v3 = serializers.FloatField(required=False)
    cvss_vector = serializers.CharField(required=False)
    severity = serializers.CharField()
    published = serializers.DateTimeField(required=False)
    modified = serializers.DateTimeField(required=False)
    last_modified = serializers.DateTimeField(required=False)
    references = serializers.ListField(child=serializers.CharField(), required=False)
    vulnerable_products = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    cwe = serializers.CharField(required=False)
    # Our tracking data
    seen_in_articles = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    first_seen_in_feed = serializers.DateTimeField(required=False)

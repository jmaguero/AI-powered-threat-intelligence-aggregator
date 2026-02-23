from django_filters import rest_framework as filters

from feeds.models import Article, IOC


class ArticleFilter(filters.FilterSet):
    source = filters.CharFilter(field_name="source", lookup_expr="iexact")
    published_after = filters.DateTimeFilter(field_name="published_date", lookup_expr="gte")
    published_before = filters.DateTimeFilter(field_name="published_date", lookup_expr="lte")
    threat_type = filters.CharFilter(field_name="threat_type", lookup_expr="icontains")
    severity = filters.CharFilter(field_name="severity", lookup_expr="iexact")
    affected_tech = filters.CharFilter(field_name="affected_tech", lookup_expr="icontains")

    class Meta:
        model = Article
        fields = ["source", "published_after", "published_before", "threat_type", "severity", "affected_tech"]


class IOCFilter(filters.FilterSet):
    ioc_type = filters.ChoiceFilter(choices=IOC.IOC_TYPES)
    value = filters.CharFilter(lookup_expr='icontains')
    confidence = filters.ChoiceFilter(choices=IOC.CONFIDENCE_LEVELS)
    first_seen_after = filters.DateTimeFilter(field_name='first_seen', lookup_expr='gte')
    first_seen_before = filters.DateTimeFilter(field_name='first_seen', lookup_expr='lte')
    min_times_seen = filters.NumberFilter(field_name='times_seen', lookup_expr='gte')
    is_validated = filters.BooleanFilter()
    is_false_positive = filters.BooleanFilter()

    class Meta:
        model = IOC
        fields = ['ioc_type', 'value', 'confidence', 'is_validated', 'is_false_positive']

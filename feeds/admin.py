from django.contrib import admin

from feeds.models import Article, IOC


class IOCAdmin(admin.ModelAdmin):
    list_display = [
        "value",
        "ioc_type",
        "confidence",
        "times_seen",
        "first_seen",
        "is_validated",
        "is_false_positive",
    ]
    list_filter = ["ioc_type", "confidence", "is_validated", "is_false_positive"]
    search_fields = ["value"]
    readonly_fields = ["first_seen", "last_seen", "times_seen"]
    filter_horizontal = ["articles"]


admin.site.register(Article)
admin.site.register(IOC, IOCAdmin)

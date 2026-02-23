from django.db import models
from django.utils import timezone


class Article(models.Model):
    title = models.CharField(max_length=512)
    published_date = models.DateTimeField(null=True, blank=True)
    link = models.URLField(max_length=1024, unique=True)
    summary = models.TextField(blank=True, default="")
    source = models.CharField(max_length=128, default="CISA")
    created_at = models.DateTimeField(auto_now_add=True)

    # AI-generated fields
    ai_summary = models.TextField(blank=True, default="")
    threat_type = models.CharField(max_length=256, blank=True, default="")
    severity = models.CharField(max_length=64, blank=True, default="")
    affected_tech = models.CharField(max_length=512, blank=True, default="")
    enriched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["link"]),
            models.Index(fields=["source"]),
            models.Index(fields=["published_date"]),
            models.Index(fields=["source", "published_date"]),
            models.Index(fields=["threat_type"]),
            models.Index(fields=["severity"]),
        ]
        ordering = ["-published_date"]

    def __str__(self):
        return self.title


class IOC(models.Model):
    """Indicator of Compromise extracted from threat intelligence articles."""

    IOC_TYPES = [
        ("ip", "IP Address"),
        ("domain", "Domain"),
        ("url", "URL"),
        ("md5", "MD5 Hash"),
        ("sha1", "SHA1 Hash"),
        ("sha256", "SHA256 Hash"),
        ("cve", "CVE Identifier"),
        ("email", "Email Address"),
    ]

    CONFIDENCE_LEVELS = [
        ("high", "High"),  # Regex validated
        ("medium", "Medium"),  # LLM extracted
        ("low", "Low"),  # Needs review
    ]

    value = models.CharField(max_length=512, db_index=True)
    ioc_type = models.CharField(max_length=16, choices=IOC_TYPES, db_index=True)
    confidence = models.CharField(
        max_length=16, choices=CONFIDENCE_LEVELS, default="medium"
    )
    context = models.TextField(blank=True, default="")  # Surrounding text from article

    # Relationships
    articles = models.ManyToManyField(Article, related_name="iocs")

    # Tracking metadata
    first_seen = models.DateTimeField(default=timezone.now, db_index=True)
    last_seen = models.DateTimeField(default=timezone.now)
    times_seen = models.PositiveIntegerField(default=1)

    # Quality flags
    is_validated = models.BooleanField(default=False)
    is_false_positive = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["ioc_type", "value"]),
            models.Index(fields=["ioc_type", "confidence"]),
            models.Index(fields=["first_seen"]),
            models.Index(fields=["times_seen"]),
        ]
        ordering = ["-first_seen"]
        verbose_name = "IOC"
        verbose_name_plural = "IOCs"

    def __str__(self):
        return f"{self.ioc_type.upper()}: {self.value}"

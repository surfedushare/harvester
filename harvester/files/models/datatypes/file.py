import re
from urllib.parse import urlparse
from mimetypes import guess_type

from django.db import models
from django.conf import settings

from core.models.datatypes.document import HarvestDocument
from core.models.datatypes.overwrite import HarvestOverwrite


def default_document_tasks():
    return {
        "tika": {
            "depends_on": ["url"],
            "checks": []
        },
        "extruct": {
            "depends_on": ["url"],
            "checks": ["!is_not_found"]
        },
        "pdf_thumbnail": {
            "depends_on": ["url"],
            "checks": ["!is_not_found"]
        },
        "video_thumbnail": {
            "depends_on": ["url"],
            "checks": ["!is_not_found", "is_video"]
        }
    }


youtube_domain_regex = re.compile(r".*(youtube\.com|youtu\.be)", re.IGNORECASE)


TECHNICAL_TYPE_CHOICES = [
    (technical_type, technical_type.capitalize())
    for technical_type in set(settings.MIME_TYPE_TO_TECHNICAL_TYPE.values())
]


class FileDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)

    domain = models.CharField(max_length=256, null=True, blank=True)
    mime_type = models.CharField(max_length=256, null=True, blank=True)
    type = models.CharField(max_length=50, choices=TECHNICAL_TYPE_CHOICES, default="unknown")
    is_not_found = models.BooleanField(default=False)

    @property
    def is_youtube_video(self):
        return youtube_domain_regex.match(self.domain)

    @property
    def is_video(self):
        return self.is_youtube_video

    @property
    def is_pdf(self):
        return self.mime_type in ["application/pdf", "application/x-pdf"]

    def clean(self):
        url = self.properties.get("url", None)
        if url:
            url_info = urlparse(url)
            self.domain = url_info.hostname
        mime_type = self.properties.get("mime_type")
        if not mime_type and url:
            mime_type, encoding = guess_type(url)
        self.mime_type = mime_type
        if self.mime_type:
            self.type = settings.MIME_TYPE_TO_TECHNICAL_TYPE[self.mime_type]


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "file overwrite"
        verbose_name_plural = "file overwrites"

import re
from urllib.parse import urlparse
from mimetypes import guess_type

from django.db import models
from django.conf import settings

from datagrowth.resources.base import Resource

from core.models.datatypes import HarvestDocument, HarvestOverwrite
from files.models.resources.metadata import HttpTikaResource


def default_document_tasks():
    return {
        "tika": {
            "depends_on": ["$.url"],
            "checks": ["!is_invalid"],
            "resources": ["files.HttpTikaResource"]
        },
        "extruct": {
            "depends_on": ["tika"],
            "checks": ["is_youtube_video"],
            "resources": ["files.ExtructResource"]
        },
        "pdf_preview": {
            "depends_on": ["tika"],
            "checks": ["is_pdf"],
            "resources": ["files.PdfThumbnailResource"]
        },
        "video_preview": {
            "depends_on": ["tika"],
            "checks": ["is_video"],
            "resources": ["files.YoutubeThumbnailResource"]
        }
    }


youtube_domain_regex = re.compile(r".*(youtube\.com|youtu\.be)", re.IGNORECASE)


TECHNICAL_TYPE_CHOICES = sorted([
    (technical_type, technical_type.capitalize())
    for technical_type in set(settings.MIME_TYPE_TO_TECHNICAL_TYPE.values())
], key=lambda choice: choice[1])


WHITELISTED_OUTPUT_FIELDS = {
    "srn", "url", "hash", "state", "title", "type", "is_link", "copyright", "mime_type", "access_rights"
}


class FileDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)

    domain = models.CharField(max_length=256, null=True, blank=True)
    mime_type = models.CharField(max_length=256, null=True, blank=True)
    type = models.CharField(max_length=50, choices=TECHNICAL_TYPE_CHOICES, default="unknown")
    is_not_found = models.BooleanField(default=False)
    is_analysis_allowed = models.BooleanField(null=True, blank=True)
    is_invalid = models.BooleanField(default=False)

    def apply_resource(self, resource: Resource):
        if isinstance(resource, HttpTikaResource):
            if resource.status == 404:
                self.is_not_found = True
                self.pending_at = None

    @property
    def is_youtube_video(self):
        if not self.domain:
            return False
        return youtube_domain_regex.match(self.domain)

    @property
    def is_video(self):
        """
        This property controls whether we'll be dispatching the video_preview task.
        We only make previews for a very limited amount of video sources at the moment.
        """
        return self.is_youtube_video or (self.domain and self.domain.startswith("vimeo.com"))

    @property
    def is_pdf(self):
        return self.mime_type in ["application/pdf", "application/x-pdf"]

    def get_analysis_allowed(self) -> bool:
        match self.properties.get("access_rights", None), self.properties.get("copyright", None):
            case "OpenAccess", _:
                return True
            case "RestrictedAccess", copyright_:
                return copyright_ and copyright_ not in ["yes", "unknown"] and "nd" not in copyright_
            case "ClosedAccess", _:
                return False
        return False

    def clean(self):
        super().clean()
        url = self.properties.get("url", None)
        if url and not url.startswith("http"):
            self.is_invalid = True
        elif url:
            url_info = urlparse(url)
            self.domain = url_info.hostname
        else:
            self.is_invalid = True
        mime_type = self.properties.get("mime_type")
        if not mime_type and url:
            mime_type, encoding = guess_type(url)
        self.mime_type = mime_type
        if self.mime_type:
            self.type = settings.MIME_TYPE_TO_TECHNICAL_TYPE.get(self.mime_type, "unknown")
            self.properties["type"] = self.type
        self.is_analysis_allowed = self.get_analysis_allowed()

    def to_data(self, merge_derivatives: bool = True) -> dict:
        data = {
            key: value
            for key, value in super().to_data(merge_derivatives=False).items() if key in WHITELISTED_OUTPUT_FIELDS
        }
        if "tika" in self.derivatives:
            data["text"] = self.derivatives["tika"]["texts"][0]  # TODO: allow all Tika output
        if "extruct" in self.derivatives:
            data["video"] = self.derivatives["extruct"]
        if "pdf_preview" in self.derivatives:
            data["previews"] = self.derivatives["pdf_preview"]
        elif "video_preview" in self.derivatives:
            data["previews"] = self.derivatives["video_preview"]
        return data


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "file overwrite"
        verbose_name_plural = "file overwrites"

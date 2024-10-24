import re
from urllib3.util import parse_url
from urllib3.exceptions import LocationParseError
from mimetypes import guess_type
from copy import deepcopy

from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.utils.html import strip_tags
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from datagrowth.resources.base import Resource

from core.models.datatypes import HarvestDocument, HarvestOverwrite
from files.constants import SEED_DEFAULTS
from files.models.resources.youtube_api import YoutubeAPIResource
from files.models.resources.metadata import CheckURLResource


def default_document_tasks():
    return {
        "check_url": {
            "depends_on": ["$.hash"],
            "checks": ["!is_not_found", "is_analysis_allowed", "!is_youtube_video"],
            "resources": ["files.CheckURLResource"]
        },
        "tika": {
            "depends_on": ["$.hash", "check_url"],
            "checks": ["is_analysis_possible"],
            "resources": ["files.HttpTikaResource"]
        },
        "pdf_preview": {
            "depends_on": ["$.hash", "check_url"],
            "checks": ["is_analysis_possible", "is_pdf"],
            "resources": ["files.PdfThumbnailResource"]
        },
        "image_preview": {
            "depends_on": ["$.hash", "check_url"],
            "checks": ["is_analysis_possible", "is_image"],
            "resources": ["files.ImageThumbnailResource"]
        },
        "video_preview": {
            # While thumbnails from Youtube API get ignored we need this task to be lenient.
            # It would be better to perform a check_url and use is_analysis_possible before executing,
            # but that fails for Youtube so that's not a possibility at the moment.
            "depends_on": [],
            "checks": ["is_video"],
            "resources": ["files.YoutubeThumbnailResource"]
        },
        "youtube_api": {
            "depends_on": ["$.hash"],
            "checks": ["is_youtube_video"],
            "resources": ["files.YoutubeAPIResource"]
        }
    }


youtube_domain_regex = re.compile(r".*(youtube\.com|youtu\.be)", re.IGNORECASE)
url_validator = URLValidator()


TECHNICAL_TYPE_CHOICES = sorted([
    (technical_type, technical_type.capitalize())
    for technical_type in set(settings.MIME_TYPE_TO_TECHNICAL_TYPE.values())
], key=lambda choice: choice[1])


WHITELISTED_OUTPUT_FIELDS = {
    "srn", "url", "hash", "state", "title", "type", "is_link", "copyright", "mime_type", "access_rights", "priority",
    "language", "provider",
}


class Redirects(models.TextChoices):
    EXCLUSIVE_PERMANENT = "exclusive_permanent", "Exclusively permanent redirects"
    TEMPORARY = "temporary", "At least one temporary redirect"
    NO = "no", "No redirects"


class FileDocument(HarvestDocument):

    tasks = models.JSONField(default=default_document_tasks, blank=True)

    status_code = models.SmallIntegerField(default=-1)
    redirects = models.CharField(max_length=50, choices=Redirects.choices, default=Redirects.NO, db_index=True)
    domain = models.CharField(max_length=256, null=True, blank=True)
    mime_type = models.CharField(max_length=256, null=True, blank=True, db_index=True)
    type = models.CharField(max_length=50, choices=TECHNICAL_TYPE_CHOICES, default="unknown", db_index=True)
    is_not_found = models.BooleanField(default=False, db_index=True)
    is_analysis_allowed = models.BooleanField(null=True, blank=True, db_index=True)

    property_defaults = SEED_DEFAULTS

    def apply_resource(self, resource: Resource):
        if isinstance(resource, CheckURLResource):
            _, content = resource.content
            content = content or {}
            if status := content.get("status"):
                self.status_code = status or 0
            if content.get("has_temporary_redirect"):
                self.redirects = Redirects.TEMPORARY
            elif content.get("has_redirect"):
                self.redirects = Redirects.EXCLUSIVE_PERMANENT
        if isinstance(resource, (CheckURLResource, YoutubeAPIResource)):
            if resource.status == 404:
                self.is_not_found = True
                self.pending_at = None
                self.finished_at = now()

    @property
    def is_link(self):
        return self.properties.get("is_link", False)

    @property
    def is_youtube_video(self):
        url = self.properties.get("url")
        if not self.domain or not url:
            return False
        return youtube_domain_regex.match(self.domain) and YoutubeAPIResource.url_to_id(url)

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

    @property
    def is_image(self):
        if self.type != "image":
            return False
        content_type = self.derivatives.get("check_url", {}).get("content_type")
        return bool(content_type and content_type != "text/html")

    @property
    def is_analysis_possible(self):
        check_url = self.derivatives.get("check_url", {})
        status = check_url.get("status")
        return status is not None and 200 <= status < 209

    def get_analysis_allowed(self) -> bool:
        match self.properties.get("access_rights", None), self.properties.get("copyright", None):
            case "OpenAccess", _:
                return True
            case "RestrictedAccess", copyright_:
                return copyright_ and copyright_ not in ["yes", "unknown"] and "nd" not in copyright_
            case "ClosedAccess", _:
                return False
        return False

    def clean(self, set_metadata=True):
        super().clean(set_metadata=set_metadata)
        url = self.properties.get("url", None)
        try:
            url_validator(url)
            scheme, auth, host, port, path, query, fragment = parse_url(url)
            self.domain = host
        except (ValidationError, LocationParseError):
            self.is_not_found = True
        mime_type = self.properties.get("mime_type")
        if not mime_type and url:
            mime_type, encoding = guess_type(url)
        self.mime_type = mime_type
        self.type = settings.MIME_TYPE_TO_TECHNICAL_TYPE.get(self.mime_type, "unknown")
        self.properties["type"] = self.type
        self.is_analysis_allowed = self.get_analysis_allowed()

    def to_data(self, merge_derivatives: bool = True, use_multilingual_fields: bool = False) -> dict:
        raw_data = super().to_data(merge_derivatives=False, use_multilingual_fields=use_multilingual_fields)
        data = {
            key: value
            for key, value in raw_data.items() if key in WHITELISTED_OUTPUT_FIELDS
        }
        if "tika" in self.derivatives:
            text = strip_tags(self.derivatives["tika"]["texts"][0])
            if text and len(text) >= 1000000:
                text = " ".join(text.split(" ")[:10000])
            data["text"] = text
        if "youtube_api" in self.derivatives:
            youtube_data = deepcopy(self.derivatives["youtube_api"])
            data["video"] = youtube_data
        if "pdf_preview" in self.derivatives:
            data["previews"] = self.derivatives["pdf_preview"]
        elif "video_preview" in self.derivatives:
            data["previews"] = self.derivatives["video_preview"]
        elif "image_preview" in self.derivatives:
            data["previews"] = self.derivatives["image_preview"]
        return data


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "file overwrite"
        verbose_name_plural = "file overwrites"

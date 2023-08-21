import os
from io import BytesIO
from urllib.parse import urlparse, urljoin
from datetime import datetime

from django.conf import settings
from django.dispatch import receiver
from django.db import models
from django.contrib.contenttypes.models import ContentType

import pdf2image
from pdf2image.exceptions import PDFPageCountError
from versatileimagefield.fields import VersatileImageField
from versatileimagefield.utils import build_versatileimagefield_url_set

from datagrowth.resources import HttpFileResource


class BasePdfThumbnailResource(HttpFileResource):

    def _update_from_results(self, response):
        # Save the metadata
        self.head = dict(response.headers.lower_items())
        self.status = response.status_code
        # Get the image file we want to save
        file = BytesIO(response.content)
        try:
            image = pdf2image.convert_from_bytes(file.read(), single_file=True, fmt="png")[0]
        except PDFPageCountError:
            self.status = 1
            return
        # Defer a file name from the URL
        path = urlparse(response.url).path
        tail, head = os.path.split(path)
        if not head:
            head = "index.png"
        name, extension = os.path.splitext(head)
        extension = ".png"
        now = datetime.utcnow()
        if len(name) > 60:
            name = name[len(name) - 60:]
        file_name = self.get_file_name(f"{name}{extension}", now)
        # Save to instance
        self.preview.save(file_name, image.fp)

    @property
    def content(self):
        if self.success:
            signed_urls = build_versatileimagefield_url_set(self.preview, [
                ('full_size', 'url'),
                ('preview', 'thumbnail__400x300'),
                ('preview_small', 'thumbnail__200x150'),
            ])
            return "application/json", {
                image_key: urljoin(url, urlparse(url).path)
                for image_key, url in signed_urls.items()
            }
        return None, None

    class Meta:
        abstract = True


class PdfThumbnailResource(BasePdfThumbnailResource):

    preview = VersatileImageField(upload_to=os.path.join("files", "previews", "pdf"), null=True, blank=True)
    retainer_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE, related_name="+")

    class Meta:
        app_label = "files"


@receiver(models.signals.post_delete, sender=PdfThumbnailResource)
def delete_pdf_thumbnail_images(sender, instance, **kwargs):
    if instance.preview:
        # Deletes images from VersatileImageField
        instance.preview.delete_all_created_images()
        # Deletes original image
        instance.preview.delete(save=False)

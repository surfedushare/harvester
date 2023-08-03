import logging
import os

from django.db import models
from django.dispatch import receiver
from versatileimagefield.fields import VersatileImageField

from files.models.resources.youtube_thumbnail import BaseYoutubeThumbnailResource
from files.models.resources.pdf_thumbnail import BasePdfThumbnailResource


logger = logging.getLogger("harvester")


class YoutubeThumbnailResource(BaseYoutubeThumbnailResource):
    preview = VersatileImageField(upload_to=os.path.join("core", "previews", "youtube"), null=True, blank=True)


class PdfThumbnailResource(BasePdfThumbnailResource):
    preview = VersatileImageField(upload_to=os.path.join("core", "previews", "pdf"), null=True, blank=True)


@receiver(models.signals.post_delete, sender=YoutubeThumbnailResource)
def delete_youtube_thumbnail_images(sender, instance, **kwargs):
    if instance.preview:
        # Deletes images from VersatileImageField
        try:
            instance.preview.delete_all_created_images()
        except AssertionError:
            logger.warning(f"AssertionError when deleting images for YoutubeThumbnailResource {instance.id}")
        # Deletes original image
        instance.preview.delete(save=False)


@receiver(models.signals.post_delete, sender=PdfThumbnailResource)
def delete_pdf_thumbnail_images(sender, instance, **kwargs):
    if instance.preview:
        # Deletes images from VersatileImageField
        instance.preview.delete_all_created_images()
        # Deletes original image
        instance.preview.delete(save=False)

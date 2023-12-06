from django.core.management.base import BaseCommand

from core.logging import HarvestLogger
from core.models.resources.utils import extend_resource_cache


class Command(BaseCommand):
    """
    A convenience command to extend validity of Resources
    """

    resources = [
        "core.HttpTikaResource",
        "core.ExtructResource",
        "core.YoutubeThumbnailResource",
        "core.PdfThumbnailResource",
    ]

    def handle(self, **options):
        logger = HarvestLogger(None, "extend_resource_cache", {})
        task_resources = {
            "core": {
                resource: []
                for resource in self.resources
            }
        }
        for label, resource in extend_resource_cache(task_resources=task_resources):
            logger.info(f"Extended cache for: {label}.{resource.get_name()}")
        logger.info("Done extending resource cache")

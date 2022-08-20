from django.apps import AppConfig
from django.conf import settings

from datagrowth.configuration import register_defaults


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):

        register_defaults("global", {
            "purge_after": {"days": 30},
            "pipeline_app_label": None,
            "pipeline_models": {
                "document": "Document",
                "process_result": "ProcessResult",
                "batch": "Batch"
            },
        })
        register_defaults("micro_service", {
            "connections": {
                "analyzer": {
                    "protocol": "http",
                    "host": "localhost:9090" if settings.IS_AWS or settings.CONTEXT != "container" else "analyzer:9090",
                    "path": "/analyze"
                }
            }
        })
        register_defaults("http_resource", {
            "method": "get"
        })
        register_defaults("extract_processor", {
            "extractor": "ExtractProcessor.extract_from_resource",
            "to_property": None
        })

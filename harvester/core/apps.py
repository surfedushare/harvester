from django.apps import AppConfig

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
        register_defaults("http_resource", {
            "method": "get"
        })
        register_defaults("extract_processor", {
            "extractor": "ExtractProcessor.extract_from_resource",
            "to_property": None
        })

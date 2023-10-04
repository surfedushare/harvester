from django.apps import AppConfig

from datagrowth.configuration import register_defaults


class CoreConfig(AppConfig):
    name = 'core'
    document_model = 'Document'

    def ready(self):

        register_defaults("global", {
            "batch_size": 100,
            "purge_after": {"days": 30},
            "pipeline_depends_on": None,
            "pipeline_app_label": None,
            "pipeline_models": {
                "document": "Document",
                "process_result": "ProcessResult",
                "batch": "Batch"
            },
        })
        register_defaults("http_resource", {
            "method": "get",
            "continuation_limit": 9999  # an arbitrary large number to never hit this limit
        })
        register_defaults("extract_processor", {
            "extractor": "ExtractProcessor.extract_from_resource",
            "to_property": None,
            "apply_resource_to": []
        })
        register_defaults("seeding_processor", {
            "phase": "initial",
            "phases": [],
            "identifier": "srn",  # SURF Resource Name
            "is_post_initialization": False
        })

from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.processors import HttpPipelineProcessor
from files.models import FileDocument


@app.task(name="tika", base=DatabaseConnectionResetTask)
def tika_task(document_ids: list[int]) -> None:

    def texts_extraction(results):
        return [
            result.get("X-TIKA:content", None)
            for result in results
        ]

    tika_processor = HttpPipelineProcessor({
        "pipeline_app_label": "files",
        "pipeline_models": {
            "document": "FileDocument",
            "process_result": "ProcessResult",
            "batch": "Batch"
        },
        "pipeline_phase": "tika",
        "batch_size": len(document_ids),
        "asynchronous": False,
        "retrieve_data": {
            "resource": "files.httptikaresource",
            "method": "put",
            "args": ["$.url"],
            "kwargs": {},
        },
        "contribute_data": {
            "to_property": "derivatives/tika",
            "apply_resource_to": ["is_not_found", "pending_at"],
            "objective": {
                "@": "$",
                "#texts": texts_extraction,
            }
        }
    })
    tika_processor(FileDocument.objects.filter(id__in=document_ids))


@app.task(name="extruct", base=DatabaseConnectionResetTask)
def extruct_task(document_ids: list[int]) -> None:
    extruct_processor = HttpPipelineProcessor({
        "pipeline_app_label": "files",
        "pipeline_models": {
            "document": "FileDocument",
            "process_result": "ProcessResult",
            "batch": "Batch"
        },
        "pipeline_phase": "extruct",
        "batch_size": len(document_ids),
        "asynchronous": False,
        "retrieve_data": {
            "resource": "files.extructresource",
            "method": "get",
            "args": ["$.url"],
            "kwargs": {},
        },
        "contribute_data": {
            "to_property": "derivatives/extruct",
            "objective": {
                "@": "$.microdata",
                "duration": "$.properties.duration",
                "embed_url": "$.properties.embedUrl"
            }
        }
    })
    extruct_processor(FileDocument.objects.filter(id__in=document_ids))

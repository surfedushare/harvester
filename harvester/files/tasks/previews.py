from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models
from core.processors import HttpPipelineProcessor, ShellPipelineProcessor


@app.task(name="video_preview", base=DatabaseConnectionResetTask)
def video_preview(app_label: str, document_ids: list[int]):
    models = load_harvest_models(app_label)
    FileDocument = models["Document"]
    youtube_dl_processor = ShellPipelineProcessor({
        "pipeline_app_label": "files",
        "pipeline_models": {
            "document": "FileDocument",
            "process_result": "ProcessResult",
            "batch": "Batch"
        },
        "pipeline_phase": "video_preview",
        "asynchronous": False,
        "retrieve_data": {
            "resource": "files.youtubethumbnailresource",
            "args": ["$.url"],
            "kwargs": {},
        },
        "contribute_data": {
            "to_property": "derivatives/video_preview",
            "objective": {
                "@": "$",
                "full_size": "$.full_size",
                "preview": "$.preview",
                "preview_small": "$.preview_small",
            }
        }
    })
    youtube_dl_processor(FileDocument.objects.filter(id__in=document_ids))


@app.task(name="pdf_preview", base=DatabaseConnectionResetTask)
def pdf_preview(app_label: str, document_ids: list[int]):
    models = load_harvest_models(app_label)
    FileDocument = models["Document"]
    pdf_processor = HttpPipelineProcessor({
        "pipeline_app_label": "files",
        "pipeline_models": {
            "document": "FileDocument",
            "process_result": "ProcessResult",
            "batch": "Batch"
        },
        "pipeline_phase": "pdf_preview",
        "batch_size": len(document_ids),
        "asynchronous": False,
        "retrieve_data": {
            "resource": "files.pdfthumbnailresource",
            "method": "get",
            "args": ["$.url"],
            "kwargs": {},
        },
        "contribute_data": {
            "to_property": "derivatives/pdf_preview",
            "objective": {
                "@": "$",
                "full_size": "$.full_size",
                "preview": "$.preview",
                "preview_small": "$.preview_small",
            }
        }
    })
    pdf_processor(FileDocument.objects.filter(id__in=document_ids))


@app.task(name="pdf_preview", base=DatabaseConnectionResetTask)
def image_preview(app_label: str, document_ids: list[int]):
    models = load_harvest_models(app_label)
    FileDocument = models["Document"]
    image_processor = HttpPipelineProcessor({
        "pipeline_app_label": "files",
        "pipeline_models": {
            "document": "FileDocument",
            "process_result": "ProcessResult",
            "batch": "Batch"
        },
        "pipeline_phase": "image_preview",
        "batch_size": len(document_ids),
        "asynchronous": False,
        "retrieve_data": {
            "resource": "files.imagethumbnailresource",
            "method": "get",
            "args": ["$.url"],
            "kwargs": {},
        },
        "contribute_data": {
            "to_property": "derivatives/image_preview",
            "objective": {
                "@": "$",
                "full_size": "$.full_size",
                "preview": "$.preview",
                "preview_small": "$.preview_small",
            }
        }
    })
    image_processor(FileDocument.objects.filter(id__in=document_ids))

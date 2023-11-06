import re

from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.processors import HttpPipelineProcessor
from core.loading import load_harvest_models


def tika_content_extraction(results):
    return [
        result.get("X-TIKA:content", "").strip()
        for result in results
    ]


@app.task(name="tika", base=DatabaseConnectionResetTask)
def tika_task(app_label: str, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Document = models["Document"]

    tika_processor = HttpPipelineProcessor({
        "pipeline_app_label": app_label,
        "pipeline_models": {
            "document": Document._meta.model_name,
            "process_result": "ProcessResult",
            "batch": "Batch"
        },
        "pipeline_phase": "tika",
        "batch_size": len(document_ids),
        "asynchronous": False,
        "retrieve_data": {
            "tika_return_type": "text",
            "resource": "files.httptikaresource",
            "method": "put",
            "args": ["$.url"],
            "kwargs": {},
        },
        "contribute_data": {
            "to_property": "derivatives/tika",
            "apply_resource_to": ["is_not_found", "pending_at", "finished_at"],
            "objective": {
                "@": "$",
                "#texts": tika_content_extraction,
            }
        }
    })
    tika_processor(Document.objects.filter(id__in=document_ids))


@app.task(name="tika_xml", base=DatabaseConnectionResetTask)
def tika_xml_task(app_label: str, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    Document = models["Document"]

    tika_xml_processor = HttpPipelineProcessor({
        "pipeline_app_label": app_label,
        "pipeline_models": {
            "document": Document._meta.model_name,
            "process_result": "ProcessResult",
            "batch": "Batch"
        },
        "pipeline_phase": "tika_xml",
        "batch_size": len(document_ids),
        "asynchronous": False,
        "retrieve_data": {
            "tika_return_type": "xml",
            "resource": "files.httptikaresource",
            "method": "put",
            "args": ["$.url"],
            "kwargs": {},
        },
        "contribute_data": {
            "to_property": "derivatives/tika_xml",
            "objective": {
                "@": "$",
                "#xmls": tika_content_extraction,
            }
        }
    })
    tika_xml_processor(Document.objects.filter(id__in=document_ids))


@app.task(name="extruct", base=DatabaseConnectionResetTask)
def extruct_task(app_label, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    FileDocument = models["Document"]
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


def get_embed_url(node):
    html = node["player"]["embedHtml"]
    url_regex = re.findall(r'src=\\?"\/?\/?(.*?)\\?"', html)  # finds the string withing src: src="<string>"
    if not url_regex:
        return
    return url_regex[0]


def get_previews(node):
    thumbnails = node["snippet"]["thumbnails"]
    if "maxres" in thumbnails:
        full_size_key = "maxres"
    elif "standard" in thumbnails:
        full_size_key = "standard"
    else:
        full_size_key = "default"
    return {
        "full_size": thumbnails[full_size_key]["url"],
        "preview": thumbnails["high"]["url"],
        "preview_small": thumbnails["medium"]["url"]
    }


@app.task(name="youtube_api", base=DatabaseConnectionResetTask)
def youtube_api_task(app_label, document_ids: list[int]) -> None:
    models = load_harvest_models(app_label)
    FileDocument = models["Document"]
    youtube_api_processor = HttpPipelineProcessor({
        "pipeline_app_label": "files",
        "pipeline_models": {
            "document": "FileDocument",
            "process_result": "ProcessResult",
            "batch": "Batch"
        },
        "pipeline_phase": "youtube_api",
        "batch_size": len(document_ids),
        "asynchronous": False,
        "retrieve_data": {
            "resource": "files.youtubeapiresource",
            "method": "get",
            "args": ["$.url", "videos"],
            "kwargs": {},
        },
        "contribute_data": {
            "to_property": "derivatives/youtube_api",
            "apply_resource_to": ["is_not_found", "pending_at", "finished_at"],
            "objective": {
                "@": "$.items.0",
                "description": "$.snippet.description",
                "duration": "$.contentDetails.duration",
                "definition": "$.contentDetails.definition",
                "license": "$.status.license",
                "embed_url": get_embed_url,
                "previews": get_previews
            }
        }
    })
    youtube_api_processor(FileDocument.objects.filter(id__in=document_ids))

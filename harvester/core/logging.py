import logging
from copy import copy

from django.conf import settings


harvester = logging.getLogger('harvester')
documents = logging.getLogger('documents')
results = logging.getLogger('results')


class HarvestLogger(object):

    dataset = None
    command = None
    command_options = None
    warn_delete_does_not_exist = True

    def __init__(self, dataset, command, command_options, is_legacy_logger=True, warn_delete_does_not_exist=True):
        self.dataset = dataset
        self.command = command
        self.command_options = command_options
        self.is_legacy_logger = is_legacy_logger
        self.warn_delete_does_not_exist = warn_delete_does_not_exist

    def _get_extra_info(self, entity=None, phase=None, progress=None, document=None, result=None):
        return {
            "dataset": self.dataset,
            "command": self.command,
            "command_options": self.command_options,
            "version": settings.VERSION,
            "commit": settings.GIT_COMMIT,
            "entity": entity,
            "phase": phase,
            "progress": progress,
            "document": document,
            "result": result or {},
            "legacy_logger": self.is_legacy_logger,
            "project": settings.PROJECT,
        }

    def debug(self, message):
        extra = self._get_extra_info()
        harvester.debug(message, extra=extra)

    def info(self, message):
        extra = self._get_extra_info()
        harvester.info(message, extra=extra)

    def warning(self, message):
        extra = self._get_extra_info()
        harvester.warning(message, extra=extra)

    def error(self, message):
        extra = self._get_extra_info()
        harvester.error(message, extra=extra)

    def report_document(self, external_id, entity, title=None, url=None, pipeline=None, state="upsert"):
        document_info = {
            "external_id": external_id,
            "title": title,
            "url": url
        }
        pipeline = pipeline or {}
        # Report on pipeline steps
        for task, task_result in pipeline.items():
            document = copy(document_info)
            document.update({
                "task": task,
                "success": task_result["success"],
            })
            if "resource" in task_result:
                document.update({
                    "resource": task_result["resource"],
                    "resource_id": task_result["id"]
                })
            if task_result["success"]:
                extra = self._get_extra_info(phase="report", entity=entity, document=document)
                documents.info(f"Pipeline success: {external_id}", extra=extra)
            else:
                extra = self._get_extra_info(phase="report", entity=entity, document=document)
                documents.error(f"Pipeline error: {external_id}", extra=extra)
        # Report material state
        document_info.update({
            "state": state
        })
        extra = self._get_extra_info(phase="report", entity=entity, document=document_info)
        documents.info(f"Report: {external_id}", extra=extra)

    def _get_document_counts(self, document_queryset):
        total = document_queryset.count()
        inactive_count = document_queryset.filter(properties__state="inactive").count()
        deleted_count = document_queryset.filter(properties__state="deleted").count()
        return {
            "total": total - inactive_count - deleted_count,
            "inactive_count": inactive_count,
            "deleted_count": deleted_count
        }

    def report_collection(self, collection, entity):
        document_counts = self._get_document_counts(collection.documents)
        extra = self._get_extra_info(entity=entity, result={
            "source": collection.name,
            "total": document_counts["total"],
            "deleted": document_counts["deleted_count"],
            "inactive": {
                "total": document_counts["inactive_count"]
            }
        })
        results.info(f"{collection.name} ({entity}) => {document_counts['total']}", extra=extra)

    def report_dataset_version(self, dataset_version):
        entity = dataset_version._meta.app_label
        collection_names = set()
        collection_ids = set()
        for collection in dataset_version.sets.all():
            if collection.name in collection_names:
                continue
            collection_names.add(collection.name)
            collection_ids.add(collection.id)
            self.report_collection(collection, entity)
        document_counts = self._get_document_counts(
            dataset_version.documents.filter(collection__id__in=collection_ids)
        )
        extra = self._get_extra_info(entity=entity, result={
            "source": str(dataset_version),
            "total": document_counts["total"],
            "deleted": document_counts["deleted_count"],
            "inactive": {
                "total": document_counts["inactive_count"]
            }
        })
        results.info(f"{dataset_version} ({entity}) => {document_counts['total']}", extra=extra)

    def report_cancelled_documents(self, entity, source, cancelled_count):
        extra = self._get_extra_info(entity=entity, progress="cancelled", result={
            "source": source,
            "total": cancelled_count,
        })
        results.info(f"Cancelled {source} documents ({entity}) => {cancelled_count}", extra=extra)

    def open_search_errors(self, errors):
        for error in errors:
            if "index" in error:
                self.error(f"Unable to index {error['index']['_id']}: {error['index']['error']}")
            elif "delete" in error and error["delete"]["result"] == "not_found":
                if self.warn_delete_does_not_exist:
                    self.warning(f"Unable to delete document that does not exist: {error['delete']['_id']}")
            else:
                self.error(f"Unknown open search error: {error}")

    #########################
    # LEGACY
    #########################

    def start(self, phase):
        extra = self._get_extra_info(phase=phase, progress="start")
        harvester.info(f"Starting: {phase}", extra=extra)

    def progress(self, phase, total, success=None, fail=None):
        extra = self._get_extra_info(phase=phase, progress="busy", result={
            "success": success,
            "fail": fail,
            "total": total
        })
        harvester.debug(f"Progress: {phase}", extra=extra)

    def end(self, phase, success=None, fail=None):
        extra = self._get_extra_info(phase=phase, progress="end", result={
            "success": success,
            "fail": fail,
            "total": None
        })
        harvester.info(f"Ending: {phase}", extra=extra)

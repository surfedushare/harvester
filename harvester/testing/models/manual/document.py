from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now

from datagrowth.configuration import create_config
from core.logging import HarvestLogger
from core.loading import load_source_configuration, load_harvest_models
from core.processors import HttpSeedingProcessor
from core.tasks.harvest.document import dispatch_document_tasks
from sources.models import HarvestEntity


class ManualDocument(models.Model):

    # Essential fields to be able to insert the manual document into the harvester using dispatch_manual_document
    set_specification = models.CharField(max_length=256)
    entity = models.ForeignKey(HarvestEntity, on_delete=models.CASCADE)

    properties = {}  # set by concrete models with fitting defaults

    # Some sugar fields to work easily with manual documents
    title = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.set_specification not in self.entity.set_specifications:
            raise ValidationError(
                f"{self.entity} does not specify a '{self.set_specification}' set_specification "
                f"options are: {", ".join(self.entity.set_specifications)}"
            )
        if not self.properties.get("provider"):
            self.properties["provider"] = {
                "ror": None,
                "external_id": None,
                "slug": self.entity.source.module,
                "name": self.entity.source.name
            }
        if not self.properties.get("set"):
            self.properties["set"] = f"{self.entity.source.module}:{self.set_specification}"
        if not self.properties.get("title"):
            self.properties["title"] = self.title

    class Meta:
        abstract = True


def dispatch_manual_document(document: ManualDocument, asynchronous: bool = True):
    logger = HarvestLogger("manual", "dispatch_manual_document", {}, is_legacy_logger=False)

    # Early exit for invalid documents or when manual documents are globally turned off
    if not document.properties.get("external_id"):
        # This should be a temporary condition, so we silently ignore this
        return
    if not document.entity.is_manual:
        logger.info("Did not dispatch manual document, because entity is not set to manual mode")
        return
    if not settings.ALLOW_MANUAL_DOCUMENTS:
        logger.info("Did not dispatch manual document, because it is not allowed for this environment")
        return

    # Load configuration and models
    entity_type = document.entity.type
    source_module = document.entity.source.module
    source_configuration = load_source_configuration(entity_type, source_module)
    seeding_config = create_config("seeding_processor", {
        "phases": source_configuration["seeding_phases"]
    })
    harvest_models = load_harvest_models(entity_type)
    dataset_version = harvest_models["DatasetVersion"].objects.get_current_version()
    set_name = f"{source_module}:{document.set_specification}"
    set_instance = harvest_models["Set"].objects.get(dataset_version=dataset_version, name=set_name)

    # Store seeds as documents and dispatch tasks
    current_time = now()
    seeder = HttpSeedingProcessor(set_instance, seeding_config, initial=[document.properties])
    documents = []
    for batch in seeder():
        for document in batch:
            document.prepare_task_processing(current_time=current_time)
            document.save()
            documents.append(document)
            logger.report_document(
                document.identity,
                entity_type,
                state=document.state,
                title=document.properties.get("title")
            )
    dispatch_document_tasks(entity_type, [doc.id for doc in documents], asynchronous=asynchronous)

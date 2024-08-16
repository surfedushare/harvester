from typing import Type

from django.apps import apps
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.serializers import Serializer

from search_client.constants import Entities
from search_client.opensearch import SearchClient


def load_results_serializers(request: Request, single_serializer: bool = False) -> dict[Entities, Type[Serializer]]:
    entity_presets = request.GET.get("entities", SearchClient.preset_default).split(",")
    entities = set()
    for preset in entity_presets:
        entity, config = preset.split(":")
        entities.add(entity)
    if single_serializer and len(entities) > 1:
        raise ValidationError("Entities parameter contains too many different entity types.")
    serializers = {}
    for entity_label in entities:
        try:
            app_config = apps.get_app_config(entity_label)
            serializer = app_config.result_serializer
        except (LookupError, AttributeError):
            raise ValidationError(f"Entity '{entity_label}' is not a valid entity type for search.")
        serializers[Entities(entity_label)] = serializer
    return serializers

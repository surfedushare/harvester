from typing import Type

from django.conf import settings
from django.apps import apps
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.serializers import Serializer

from search_client.constants import Entities
from search_client.opensearch import SearchClient
from search_client.opensearch.configuration import is_valid_preset_search_configuration


def validate_presets(request: Request, presets_parameter: str = "entities") -> list[str]:
    entity_inputs = request.GET.get(presets_parameter, SearchClient.preset_default).split(",")
    presets = []
    for entity_input in entity_inputs:
        try:
            preset = is_valid_preset_search_configuration(settings.PLATFORM, entity_input)
            presets.append(preset)
        except ValueError:
            raise ValidationError(f"Invalid preset '{entity_input}'.")
    return presets


def load_results_serializers(presets: list[str]) -> dict[Entities, Type[Serializer]]:
    """
    Loads serializers for given presets by looking at Django app configurations.
    """
    entities = set()
    for preset in presets:
        entity, config = preset.split(":")
        entities.add(entity)
    serializers = {}
    for entity_label in entities:
        try:
            app_config = apps.get_app_config(entity_label)
            serializer = app_config.result_serializer
        except (LookupError, AttributeError):
            raise ValidationError(f"Entity '{entity_label}' is not a valid entity type for search.")
        serializers[Entities(entity_label)] = serializer
    return serializers

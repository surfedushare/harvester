from typing import Sequence, Tuple
import logging
import json

from django.core.management import BaseCommand
from django.core.serializers import serialize
from django.db.models import Model

from metadata.models import MetadataField, MetadataValue


logger = logging.getLogger("harvester")


class Command(BaseCommand):
    """
    A command to dump metadata models to fixtures, mostly for testing and initial data purposes.
    Consider using dump_harvester_data to dump all data into a S3 bucket for sharing across environments.
    """

    excluded_value_fields = {
        "products": [
            "study_vocabulary",
            "study_vocabulary.keyword",
            "disciplines",
        ]
    }
    additional_values = {
        "products": [
            "c001f86a-4f8f-4420-bd78-381c615ecedc",  # disciplines => Aarderijskunde
            "92161d11-91ce-48e2-b79a-8aa2df8b7022",  # disciplines => Bedrijfskunde
        ]
    }

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("-e", "--entity", type=str)
        parser.add_argument("-x", "--exclude-values", action="store_true")

    @classmethod
    def _prepare_field_dump(cls, entity: str, field: MetadataField,
                            exclude_values: bool = False) -> Tuple[Sequence[Model], Sequence[Model], Sequence[Model]]:
        fields = json.loads(serialize("json", [field]))
        values = []
        translations = json.loads(serialize("json", [field.translation]))
        exclude_values = exclude_values or field.is_manual or field.english_as_dutch or \
            field.name in cls.excluded_value_fields[entity]
        if exclude_values:
            return fields, values, translations
        for root_value in MetadataValue.objects.filter(field=field, parent__isnull=True, deleted_at__isnull=True):
            branch_values = []
            branch_translations = []
            for value in root_value.get_descendants(include_self=True).filter(deleted_at__isnull=True):
                branch_values.append(value)
                branch_translations.append(value.translation)
            values.extend(
                json.loads(serialize("json", branch_values))
            )
            translations.extend(
                json.loads(serialize("json", branch_translations))
            )
        return fields, values, translations

    @classmethod
    def _prepare_additional_values_dump(cls, entity: str) -> Tuple[Sequence[Model], Sequence[Model], Sequence[Model]]:
        additional_values = cls.additional_values[entity]
        fields = []
        values = []
        translations = []
        for additional_value in MetadataValue.objects.filter(value__in=additional_values):
            branch_values = []
            branch_translations = []
            for value in additional_value.get_ancestors(include_self=True):
                branch_values.append(value)
                branch_translations.append(value.translation)
            values.extend(
                json.loads(serialize("json", branch_values))
            )
            translations.extend(
                json.loads(serialize("json", branch_translations))
            )
        return fields, values, translations

    def handle(self, **options):

        entity = options.get("entity")
        exclude_values = options.get("exclude_values", False)
        field_dumps = []
        value_dumps = []
        translation_dumps = []

        for field in MetadataField.objects.filter(entity__startswith=entity):
            fields, values, translations = self._prepare_field_dump(entity, field, exclude_values)
            field_dumps += fields
            value_dumps += values
            translation_dumps += translations

        if not exclude_values:
            fields, values, translations = self._prepare_additional_values_dump(entity)
            field_dumps += fields
            value_dumps += values
            translation_dumps += translations

        # Write to file
        logger.info("Dumping metadata")
        dump_objects = translation_dumps + field_dumps + value_dumps
        logger.info(f"Total amount of objects: {len(dump_objects)}")
        with open(f"{entity}-metadata-dump.json", "w") as json_file:
            json.dump(dump_objects, json_file, indent=4)

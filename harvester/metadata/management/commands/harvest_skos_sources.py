import logging
import polars as pl
from django.core.management.base import BaseCommand
from metadata.utils.translate import translate_with_deepl
from metadata.models import MetadataField, MetadataTranslation, MetadataValue, SkosMetadataSource


logger = logging.getLogger("harvester")


def get_or_create_metadata_value(term, field, parent) -> MetadataValue:
    try:
        return MetadataValue.objects.get(value=term["value"], field=field)
    except MetadataValue.DoesNotExist:
        pass
    translation = MetadataTranslation.objects.create(
        nl=term["name"],
        en=translate_with_deepl(term["name"]),
        is_fuzzy=True
    )
    return MetadataValue.objects.create(
        name=term["name"],
        field=field,
        parent=parent,
        value=term["value"],
        translation=translation,
        is_manual=True
    )


class Command(BaseCommand):
    """
    Some info about SKOS: https://www.forumstandaardisatie.nl/open-standaarden/skos
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--source', type=str, required=False)

    def handle(self, **options):

        source = options.get("source")

        if source is not None:
            source = SkosMetadataSource.objects.get(name=source)
            self.create_values(key=source.name, source=source)
        else:
            for source in SkosMetadataSource.objects.all():
                self.create_values(key=source.name, source=source)

    def create_values(self, key: str, source: SkosMetadataSource) -> None:
        df = (
            source.to_data_frame()
            .group_by("parent_id")
            .agg(
                pl.struct(pl.all()).alias("group")
            )
        )
        groups = {
            parent_id: group
            for parent_id, group in df.collect().select(['parent_id', 'group']).iter_rows()
        }
        for term in groups["root"]:
            self.create_values_depth_first(
                term=term,
                parent=source.parent_value,
                field=source.target_field,
                groups=groups
            )

        logger.info('Done with SKOS harvest: ' + key)

    def create_values_depth_first(self, term: dict, parent: MetadataValue, field: MetadataField,
                                  groups: dict[str, list[dict]]) -> None:
        value_instance = get_or_create_metadata_value(term=term, field=field, parent=parent)
        if term["value"] not in groups:  # no more children to process
            return
        for child_term in groups[term["value"]]:
            self.create_values_depth_first(child_term, value_instance, field, groups)

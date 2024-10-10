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

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--vocabulary',
                            choices=["applied-science", "informatievaardigheid", "vaktherapie", "verpleegkunde"])

    domain_dictionary = {
        "applied-science": {
            "path": "applied-science/applied-science-2021.skos.json",
            "nl": "Toegepaste Wetenschappen",
            "en": "Applied Science",
            "value": "applied-science",
            "name": "applied-science",
            "language": "nl"
        },
        "informatievaardigheid": {
            "path": "informatievaardigheid/informatievaardigheid-2020.skos.json",
            "nl": "Informatievaardigheid",
            "en": "Information literacy",
            "value": "informatievaardigheid",
            "name": "informatievaardigheid",
            "language": "nl"
        },
        "vaktherapie": {
            "path": "vaktherapie/vaktherapie-2020.skos.json",
            "nl": "Vaktherapie",
            "en": "Information literacy",
            "value": "vaktherapie",
            "name": "vaktherapie",
            "language": "nl"
        },
        "verpleegkunde": {
            "path": "verpleegkunde/verpleegkunde-2019.skos.json",
            "nl": "Verpleegkunde",
            "en": "Nursing",
            "value": "verpleegkunde",
            "name": "verpleegkunde",
            "language": "nl"
        },
        "ziezo-meten": {
            "path": "ziezo-meten/ziezo-meten-2022.skos.json",
            "nl": "Ziezo Meten",
            "en": "Ziezo Meten",
            "value": "ziezo-meten",
            "name": "ziezo-meten",
            "language": "nl"
        }
    }

    def handle(self, **options):

        vocabulary = options["vocabulary"]

        if vocabulary is not None:
            skos_path = self.domain_dictionary[vocabulary]["path"]
            source = SkosMetadataSource.objects.get(skos_url__endswith=skos_path)
            self.create_vocabulary(key=vocabulary, source=source)
        else:
            for key in self.domain_dictionary:
                skos_path = self.domain_dictionary[vocabulary]["path"]
                source = SkosMetadataSource.objects.get(skos_url__endswith=skos_path)
                self.create_vocabulary(key=key, source=source)

    def create_vocabulary(self, key: str, source: SkosMetadataSource) -> None:
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

        logger.info('Done with study vocabulary harvest: ' + key)

    def create_values_depth_first(self, term: dict, parent: MetadataValue, field: MetadataField,
                                  groups: dict[str, list[dict]]) -> None:
        value_instance = get_or_create_metadata_value(term=term, field=field, parent=parent)
        if term["value"] not in groups:  # no more children to process
            return
        for child_term in groups[term["value"]]:
            self.create_values_depth_first(child_term, value_instance, field, groups)

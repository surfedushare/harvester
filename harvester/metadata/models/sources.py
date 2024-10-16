import polars as pl

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models

from datagrowth.configuration import create_config
from datagrowth.processors import ExtractProcessor
from metadata.models.field import MetadataField
from metadata.models.value import MetadataValue
from metadata.models.resources.skos_vocabulary import SkosVocabularyResource


def validate_skos_json_url(value):
    if not value.endswith("skos.json"):
        raise ValidationError("URL must be a SKOS vocabulary definition")


class SkosMetadataSource(models.Model):

    name = models.CharField(max_length=255)
    skos_url = models.URLField(validators=[URLValidator(), validate_skos_json_url])
    target_field = models.ForeignKey(MetadataField, on_delete=models.CASCADE)
    parent_value = models.ForeignKey(MetadataValue, on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def to_data_frame(self) -> pl.LazyFrame:
        # Fetch the SKOS metadata
        resource = SkosVocabularyResource().get(self.skos_url)
        resource.close()
        # Transform the data using a transformation generator
        config = create_config("extract_processor", {
            "objective": {
                "@": "$.@graph",
                "value": "$.@id",
                "parent_id": "$.skos:broader.@id",
                "language": "$.skos:prefLabel.@language",
                "name": "$.skos:prefLabel.@value"
            }
        })
        extractor = ExtractProcessor(config=config)
        records = extractor.extract(*resource.content)
        # Perform some additional transformations to clean the data with a LazyFrame
        return (
            pl.LazyFrame(records)
            .drop_nulls(subset=["language", "name"])  # drops the "context" record
            # We don't allow null values for parent_id and indicate them to be a root node instead
            .with_columns(pl.col("parent_id").fill_null("root"))
            # Cast all values to strings
            .select(pl.all().cast(pl.Utf8))
        )

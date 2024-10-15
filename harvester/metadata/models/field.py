from collections import defaultdict

from django.conf import settings
from django.db import models
from rest_framework import serializers

from search_client.opensearch.configuration.presets import get_all_preset_keys, is_valid_preset_search_configuration
from search.clients import get_search_client
from metadata.models import MetadataTranslation, MetadataTranslationSerializer, MetadataValueSerializer


class MetadataFieldManager(models.Manager):

    def fetch_value_frequencies(self, **kwargs) -> dict:
        value_frequencies = {}

        # Load relevant data from the database and prepare queries
        aggregation_terms_by_entity = defaultdict(dict)
        for field in self.annotate(size=models.Count("metadatavalue")).filter(**kwargs).iterator():
            preset = is_valid_preset_search_configuration(settings.PLATFORM, field.entity)
            aggregation_terms_by_entity[preset][field.name] = {
                "terms": {
                    "field": field.name,
                    "size": field.size + 500,
                }
            }

        # Execute queries using the correct index for all terms
        for preset, terms in aggregation_terms_by_entity.items():
            client = get_search_client(presets=[preset])
            aliases = client.configuration.get_aliases()
            response = client.client.search(index=aliases, body={"aggs": terms})
            for field_name, aggregation in response["aggregations"].items():
                value_frequencies[field_name] = {
                    bucket["key"]: bucket["doc_count"]
                    for bucket in aggregation["buckets"]
                }

        return value_frequencies


ENTITY_CHOICES = [
    (key, key,) for key in get_all_preset_keys()
]


class MetadataField(models.Model):

    class ValueOutputOrders(models.TextChoices):
        FREQUENCY = "frequency"
        ALPHABETICAL = "alphabetical"
        MANUAL = "manual"

    objects = MetadataFieldManager()

    name = models.CharField(max_length=255, null=False, blank=False)
    entity = models.CharField(
        max_length=100, null=False, default="products", choices=ENTITY_CHOICES,
        help_text="Indicates which entity and/or search configuration controls metadata for this field."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    translation = models.OneToOneField(MetadataTranslation, on_delete=models.PROTECT, null=False, blank=False)
    is_hidden = models.BooleanField(default=False)
    is_manual = models.BooleanField(default=False)
    english_as_dutch = models.BooleanField(default=False)
    value_output_order = models.CharField(max_length=50, choices=ValueOutputOrders.choices,
                                          default=ValueOutputOrders.FREQUENCY)

    def __str__(self):
        return self.name

    @classmethod
    def get_name(cls):
        return cls._meta.model_name


class MetadataFieldSerializer(serializers.ModelSerializer):

    parent = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    translation = MetadataTranslationSerializer()
    value = serializers.CharField(source="name")
    frequency = serializers.SerializerMethodField()
    field = serializers.SerializerMethodField()

    max_children = serializers.IntegerField(write_only=True, required=False)

    def get_parent(self, obj):
        return None

    def get_children(self, obj):
        children = obj.metadatavalue_set.filter(is_hidden=False, deleted_at__isnull=True) \
            .select_related("translation") \
            .get_cached_trees()
        match obj.value_output_order:
            case obj.ValueOutputOrders.FREQUENCY:
                children.sort(key=lambda child: child.frequency, reverse=True)
            case obj.ValueOutputOrders.ALPHABETICAL:
                children.sort(key=lambda child: child.value)
            case _:
                pass
        max_children = self.context["request"].GET.get("max_children", "")
        max_children = int(max_children) if max_children else None
        return MetadataValueSerializer(children, many=True, context=self.context).data[:max_children]

    def get_children_count(self, obj):
        return obj.metadatavalue_set.filter(deleted_at__isnull=True, parent__isnull=True).count()

    def get_frequency(self, obj):
        aggregation = obj.metadatavalue_set.filter(deleted_at__isnull=True).aggregate(models.Sum("frequency"))
        return aggregation["frequency__sum"]

    def get_field(self, obj):
        return None

    class Meta:
        model = MetadataField
        fields = ('id', 'parent', 'is_hidden', 'is_manual', 'children', 'children_count', 'value', 'translation',
                  'frequency', 'field', 'max_children',)

# Generated by Django 4.2.14 on 2024-08-30 15:41

from copy import deepcopy

from django.conf import settings
from django.db import migrations, models

from metadata.models import MetadataField, MetadataTranslation, MetadataValue


def migrate_metadata_field_to_entities(apps, schema_editor):
    # Skipping this migration for unit test environments
    if not MetadataField.objects.all().exists():
        return

    legacy_fields = [
        "publisher_date", "study_vocabulary", "learning_material_disciplines_normalized", "language.keyword",
        "copyright.keyword", "technical_type",
    ]
    MetadataField.objects.filter(name__in=legacy_fields).update(entity="products:multilingual-indices")

    new_fields = {
        "study_vocabulary.keyword": {
            "is_manual": True,
            "is_hidden": False,
            "entity": "products:default",
        },
        "disciplines_normalized.keyword": {
            "is_manual": False,
            "is_hidden": False,
            "entity": "products:default",
        },
        "published_at": {
            "is_manual": True,
            "is_hidden": True,
            "entity": "products:default",
        },
        "modified_at": {
            "is_manual": True,
            "is_hidden": True,
            "entity": "products:default",
        },
        "language": {
            "is_manual": False,
            "is_hidden": False,
            "entity": "products:default",
        },
        "licenses": {
            "is_manual": False,
            "is_hidden": False,
            "entity": "products:default",
        },
        "technical_types": {
            "is_manual": False,
            "is_hidden": False,
            "entity": "products:default",
        }
    }
    edusources_only_fields = ["study_vocabulary.keyword", "disciplines_normalized.keyword"]
    existing_value_translation_fields = {
        "study_vocabulary.keyword": "study_vocabulary",
        "disciplines_normalized.keyword": "learning_material_disciplines_normalized",
        "language": "language.keyword",
        "licenses": "copyright.keyword",
        "technical_types": "technical_type",
    }
    for field_name, defaults in new_fields.items():
        if settings.PLATFORM.value == "publinova" and field_name in edusources_only_fields:
            continue
        # Create the field and its translation
        original_field = None
        if field_name in existing_value_translation_fields:
            original_field = MetadataField.objects.get(name=existing_value_translation_fields[field_name])
            defaults["value_output_order"] = original_field.value_output_order
            translation = original_field.translation
            translation.id = None
            translation.pk = None
            translation.created_at = None
            translation.updated_at = None
            translation.save()
        else:
            translation, _ = MetadataTranslation.objects.get_or_create(nl=field_name, en=field_name, is_fuzzy=True)
        defaults["translation"] = translation
        field, created = MetadataField.objects.get_or_create(name=field_name, defaults=defaults)
        if not created:
            field.entity = defaults["entity"]
            field.save()
        # Copy MetadataValues and share MetadataTranslations with existing fields where appropriate.
        if not original_field:
            continue
        parents_by_value = {}
        for value in MetadataValue.objects.filter(field=original_field, deleted_at__isnull=True):
            value = deepcopy(value)
            value.pk = None
            value.id = None
            value.created_at = None
            value.updated_at = None
            value.field = field
            if value.parent:
                value.parent = parents_by_value[value.parent.value]
                value.parent.save()
            translation = deepcopy(value.translation)
            translation.pk = None
            translation.id = None
            translation.created_at = None
            translation.updated_at = None
            translation.save()
            value.translation = translation
            value.save()
            parents_by_value[value.value] = value


def reverse_metadata_field_to_entities():
    from metadata.models import MetadataField, MetadataTranslation, MetadataValue
    field_names = [
        "study_vocabulary.keyword", "disciplines_normalized.keyword", "published_at", "modified_at", "language",
        "licenses", "technical_types"
    ]
    for field_name in field_names:
        field = MetadataField.objects.get(name=field_name)
        MetadataValue.objects.filter(field__name=field_name).delete()
        MetadataTranslation.objects.filter(metadatavalue__field__name=field_name).delete()
        field.delete()
        field.translation.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0006_value_output_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='metadatafield',
            name='entity',
            field=models.CharField(choices=[('products', 'products'), ('products:default', 'products:default'), ('products:multilingual-indices', 'products:multilingual-indices'), ('projects', 'projects'), ('projects:default', 'projects:default')], default='products', help_text='Indicates which entity and/or search configuration controls metadata for this field.', max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name='metadatavalue',
            unique_together={('field', 'value')},
        ),
        migrations.RemoveField(
            model_name='metadatavalue',
            name='site',
        ),
        migrations.RunPython(
            migrate_metadata_field_to_entities,
            migrations.RunPython.noop
        )
    ]

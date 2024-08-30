# Generated by Django 4.2.14 on 2024-08-30 15:41

from django.conf import settings
from django.db import migrations, models


def migrate_metadata_field_to_entities(apps, schema_editor):
    MetadataField = apps.get_model('metadata', 'MetadataField')
    MetadataTranslation = apps.get_model('metadata', 'MetadataTranslation')
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
    for field_name, defaults in new_fields.items():
        if settings.PLATFORM.value == "publinova" and field_name in edusources_only_fields:
            continue
        translation, created = MetadataTranslation.objects.get_or_create(nl=field_name, en=field_name, is_fuzzy=True)
        defaults["translation"] = translation
        field, created = MetadataField.objects.get_or_create(name=field_name, defaults=defaults)
        if not created:
            field.entity = defaults["entity"]
            field.save()


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
        migrations.RunPython(
            migrate_metadata_field_to_entities,
            migrations.RunPython.noop
        )
    ]

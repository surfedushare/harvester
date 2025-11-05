# Generated manually for adding has_material metadata field

from django.conf import settings
from django.db import migrations

from metadata.utils.operations import get_or_create_metadata_field


def add_has_material_metadata_field(apps, schema_editor):
    if settings.PLATFORM.value == "publinova":
        get_or_create_metadata_field(
            "has_material", "products:default", "Publicaties met bestand / URL", "Publications including file / URL"
        )


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0004_all_entities'),
    ]

    operations = [
        migrations.RunPython(
            add_has_material_metadata_field,
            migrations.RunPython.noop,
        )
    ]
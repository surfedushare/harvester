from django.db import migrations


def migrate_objective_to_extraction_mapping(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_dynamic_extraction'),
    ]

    operations = [
        migrations.RunPython(
            migrate_objective_to_extraction_mapping,
            migrations.RunPython.noop
        )
    ]

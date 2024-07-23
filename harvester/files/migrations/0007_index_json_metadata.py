# Generated by Django 4.2.13 on 2024-07-08 14:53

import core.models.datatypes.document
import core.utils.decoders
import django.core.serializers.json
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0006_image_previews'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filedocument',
            name='metadata',
            field=models.JSONField(blank=True, db_index=True, decoder=core.utils.decoders.HarvesterJSONDecoder, default=core.models.datatypes.document.document_metadata_default, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
    ]

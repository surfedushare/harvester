# Generated by Django 4.2.13 on 2024-07-08 14:53

import core.models.datatypes.document
import core.utils.decoders
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('testing', '0006_manual_documents'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testdocument',
            name='metadata',
            field=models.JSONField(blank=True, db_index=True, decoder=core.utils.decoders.HarvesterJSONDecoder, default=core.models.datatypes.document.document_metadata_default, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.AlterField(
            model_name='testfile',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='testing.testproduct'),
        ),
    ]

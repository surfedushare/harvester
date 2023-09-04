# Generated by Django 3.2.20 on 2023-09-04 16:57

import core.models.datatypes.dataset
import core.models.datatypes.document
import core.models.datatypes.set
import core.utils.decoders
import datagrowth.configuration.fields
import datagrowth.datatypes.documents.db.collection
import datetime
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import django.utils.timezone
import testing.models.datatypes.document


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('search', '0001_initial'),
        ('sources', '0011_harvest_sources'),
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('processor', models.CharField(max_length=256)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('is_harvested', models.BooleanField(default=False)),
                ('indexing', models.CharField(choices=[('no', 'No'), ('index_only', 'Index only'), ('index_and_promote', 'Index and promote')], default='no', max_length=50)),
            ],
            options={
                'verbose_name': 'testing dataset',
                'verbose_name_plural': 'testing datasets',
            },
        ),
        migrations.CreateModel(
            name='DatasetVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pipeline', models.JSONField(blank=True, default=dict)),
                ('derivatives', models.JSONField(blank=True, default=dict)),
                ('pending_at', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('is_current', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('version', models.CharField(blank=True, default=core.models.datatypes.dataset.version_default, max_length=50)),
                ('tasks', models.JSONField(blank=True, default=core.models.datatypes.dataset.default_dataset_version_tasks)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='testing.dataset')),
            ],
            options={
                'verbose_name': 'testing dataset version',
                'verbose_name_plural': 'testing dataset version',
            },
        ),
        migrations.CreateModel(
            name='Overwrite',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('identity', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('reference', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('properties', models.JSONField(default=dict)),
                ('deleted_at', models.DateTimeField(blank=True, default=None, null=True)),
            ],
            options={
                'verbose_name': 'test overwrite',
                'verbose_name_plural': 'test overwrites',
            },
        ),
        migrations.CreateModel(
            name='Set',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('identifier', models.CharField(blank=True, max_length=255, null=True)),
                ('referee', models.CharField(blank=True, max_length=255, null=True)),
                ('pipeline', models.JSONField(blank=True, default=dict)),
                ('derivatives', models.JSONField(blank=True, default=dict)),
                ('delete_policy', models.CharField(blank=True, choices=[('no', 'No'), ('persistent', 'Persistent'), ('transient', 'Transient')], max_length=50, null=True)),
                ('tasks', models.JSONField(blank=True, default=core.models.datatypes.set.default_set_tasks)),
                ('pending_at', models.DateTimeField(blank=True, null=True)),
                ('dataset_version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sets', to='testing.datasetversion')),
            ],
            options={
                'verbose_name': 'testing set',
                'verbose_name_plural': 'testing set',
            },
            bases=(datagrowth.datatypes.documents.db.collection.DocumentCollectionMixin, models.Model),
        ),
        migrations.CreateModel(
            name='TestDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('properties', models.JSONField(default=dict)),
                ('identity', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('reference', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('pipeline', models.JSONField(blank=True, default=dict)),
                ('derivatives', models.JSONField(blank=True, default=dict)),
                ('pending_at', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('state', models.CharField(choices=[('active', 'Active'), ('deleted', 'Deleted'), ('inactive', 'In-active'), ('skipped', 'Skipped')], default='active', max_length=50)),
                ('metadata', models.JSONField(blank=True, decoder=core.utils.decoders.HarvesterJSONDecoder, default=core.models.datatypes.document.document_metadata_default, encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('tasks', models.JSONField(blank=True, default=testing.models.datatypes.document.default_document_tasks)),
                ('is_not_found', models.BooleanField(default=False)),
                ('collection', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='document_set', to='testing.set')),
                ('dataset_version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='testing.datasetversion')),
                ('overwrite', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='testing.overwrite')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProcessResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_id', models.PositiveIntegerField(blank=True, null=True)),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testing.batch')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testing.testdocument')),
                ('result_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='overwrite',
            name='collection',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='testing.set'),
        ),
        migrations.CreateModel(
            name='MockHarvestResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uri', models.CharField(db_index=True, default=None, max_length=255)),
                ('status', models.PositiveIntegerField(default=0)),
                ('config', datagrowth.configuration.fields.ConfigurationField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('purge_at', models.DateTimeField(blank=True, null=True)),
                ('retainer_id', models.PositiveIntegerField(blank=True, null=True)),
                ('data_hash', models.CharField(blank=True, db_index=True, default='', max_length=255)),
                ('request', models.JSONField(blank=True, default=None, null=True)),
                ('head', models.JSONField(default=dict)),
                ('body', models.TextField(blank=True, default=None, null=True)),
                ('set_specification', models.CharField(blank=True, max_length=255)),
                ('since', models.DateTimeField()),
                ('retainer_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MockDetailResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uri', models.CharField(db_index=True, default=None, max_length=255)),
                ('status', models.PositiveIntegerField(default=0)),
                ('config', datagrowth.configuration.fields.ConfigurationField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('purge_at', models.DateTimeField(blank=True, null=True)),
                ('retainer_id', models.PositiveIntegerField(blank=True, null=True)),
                ('data_hash', models.CharField(blank=True, db_index=True, default='', max_length=255)),
                ('request', models.JSONField(blank=True, default=None, null=True)),
                ('head', models.JSONField(default=dict)),
                ('body', models.TextField(blank=True, default=None, null=True)),
                ('retainer_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HarvestState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('set_specification', models.CharField(help_text="The slug for the 'set' you want to harvest", max_length=255)),
                ('harvested_at', models.DateTimeField(blank=True, default=datetime.datetime(1970, 1, 1, 0, 0, tzinfo=utc))),
                ('purge_after', models.DateTimeField(blank=True, null=True)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testing.dataset')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='sources.harvestentity')),
                ('harvest_set', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='testing.set')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='datasetversion',
            name='historic_sets',
            field=models.ManyToManyField(to='testing.Set'),
        ),
        migrations.AddField(
            model_name='datasetversion',
            name='index',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='search.opensearchindex'),
        ),
        migrations.AddField(
            model_name='dataset',
            name='entities',
            field=models.ManyToManyField(related_name='_testing_dataset_entities_+', through='testing.HarvestState', to='sources.HarvestEntity'),
        ),
        migrations.AddField(
            model_name='batch',
            name='documents',
            field=models.ManyToManyField(through='testing.ProcessResult', to='testing.TestDocument'),
        ),
    ]

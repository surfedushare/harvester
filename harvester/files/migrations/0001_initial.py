# Generated by Django 3.2.20 on 2023-08-19 08:16

import core.models.datatypes.base
import core.models.datatypes.document
import datagrowth.configuration.fields
import datagrowth.datatypes.documents.db.collection
import datetime
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.utils.timezone import utc
import files.models.datatypes.file
import versatileimagefield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sources', '0011_harvest_sources'),
        ('contenttypes', '0002_remove_content_type_name'),
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
        ),
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('is_active', models.BooleanField(default=False)),
                ('is_latest', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'file dataset',
                'verbose_name_plural': 'file datasets',
            },
        ),
        migrations.CreateModel(
            name='DatasetVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metadata', models.JSONField(blank=True, default=core.models.datatypes.base.simple_metadata_default)),
                ('pipeline', models.JSONField(blank=True, default=dict)),
                ('tasks', models.JSONField(blank=True, default=dict)),
                ('derivatives', models.JSONField(blank=True, default=dict)),
                ('pending_at', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('is_current', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('version', models.CharField(blank=True, max_length=50)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='files.dataset')),
            ],
            options={
                'verbose_name': 'file dataset version',
                'verbose_name_plural': 'file dataset version',
            },
        ),
        migrations.CreateModel(
            name='FileDocument',
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
                ('metadata', models.JSONField(blank=True, default=core.models.datatypes.document.document_metadata_default)),
                ('tasks', models.JSONField(blank=True, default=files.models.datatypes.file.default_document_tasks)),
                ('domain', models.CharField(blank=True, max_length=256, null=True)),
                ('mime_type', models.CharField(blank=True, max_length=256, null=True)),
                ('type', models.CharField(choices=[('image', 'Image'), ('app', 'App'), ('document', 'Document'), ('unknown', 'Unknown'), ('website', 'Website'), ('audio', 'Audio'), ('presentation', 'Presentation'), ('video', 'Video'), ('?', '?'), ('spreadsheet', 'Spreadsheet')], default='unknown', max_length=50)),
                ('is_not_found', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='YoutubeThumbnailResource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uri', models.CharField(db_index=True, default=None, max_length=255)),
                ('status', models.PositiveIntegerField(default=0)),
                ('config', datagrowth.configuration.fields.ConfigurationField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('purge_at', models.DateTimeField(blank=True, null=True)),
                ('retainer_id', models.PositiveIntegerField(blank=True, null=True)),
                ('command', models.JSONField(blank=True, default=None, null=True)),
                ('stdin', models.TextField(blank=True, default=None, null=True)),
                ('stdout', models.TextField(blank=True, default=None, null=True)),
                ('stderr', models.TextField(blank=True, default=None, null=True)),
                ('preview', versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to='files/previews/youtube')),
                ('retainer_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.contenttype')),
            ],
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
                ('metadata', models.JSONField(blank=True, default=core.models.datatypes.base.simple_metadata_default)),
                ('pipeline', models.JSONField(blank=True, default=dict)),
                ('tasks', models.JSONField(blank=True, default=dict)),
                ('derivatives', models.JSONField(blank=True, default=dict)),
                ('pending_at', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True)),
                ('delete_policy', models.CharField(blank=True, choices=[('no', 'No'), ('persistent', 'Persistent'), ('transient', 'Transient')], max_length=50, null=True)),
                ('dataset_version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='files.datasetversion')),
            ],
            options={
                'verbose_name': 'file set',
                'verbose_name_plural': 'file set',
            },
            bases=(datagrowth.datatypes.documents.db.collection.DocumentCollectionMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ProcessResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_id', models.PositiveIntegerField(blank=True, null=True)),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='files.batch')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='files.filedocument')),
                ('result_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.contenttype')),
            ],
        ),
        migrations.CreateModel(
            name='PdfThumbnailResource',
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
                ('preview', versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to='files/previews/pdf')),
                ('retainer_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.contenttype')),
            ],
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
                ('collection', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='files.set')),
            ],
            options={
                'verbose_name': 'file overwrite',
                'verbose_name_plural': 'file overwrites',
            },
        ),
        migrations.CreateModel(
            name='HttpTikaResource',
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
                ('retainer_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.contenttype')),
            ],
        ),
        migrations.CreateModel(
            name='HarvestState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('config', datagrowth.configuration.fields.ConfigurationField()),
                ('harvested_at', models.DateTimeField(blank=True, default=datetime.datetime(1970, 1, 1, 0, 0, tzinfo=utc))),
                ('purge_after', models.DateTimeField(blank=True, null=True)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='files.dataset')),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='sources.harvestentity')),
                ('harvest_set', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='files.set')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='filedocument',
            name='collection',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='document_set', to='files.set'),
        ),
        migrations.AddField(
            model_name='filedocument',
            name='dataset_version',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='files.datasetversion'),
        ),
        migrations.AddField(
            model_name='filedocument',
            name='overwrite',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='files.overwrite'),
        ),
        migrations.CreateModel(
            name='ExtructResource',
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
                ('retainer_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.contenttype')),
            ],
        ),
        migrations.AddField(
            model_name='dataset',
            name='entities',
            field=models.ManyToManyField(through='files.HarvestState', to='sources.HarvestEntity'),
        ),
        migrations.AddField(
            model_name='batch',
            name='documents',
            field=models.ManyToManyField(through='files.ProcessResult', to='files.FileDocument'),
        ),
    ]

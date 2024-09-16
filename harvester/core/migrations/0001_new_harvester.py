# Generated by Django 4.2.15 on 2024-09-16 07:21

import core.models.search.query
import datagrowth.configuration.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('core', '0001_initial'), ('core', '0002_harvest_resources'), ('core', '0003_add_chromescreenshotresource'), ('core', '0004_add_youtubethumnbailresource'), ('core', '0005_sharekit_repository'), ('core', '0006_harvest_refactor'), ('core', '0007_harvest_refactor_data'), ('core', '0008_cleanup_command'), ('core', '0009_sharekit_speedup'), ('core', '0010_sync_lock'), ('core', '0011_harvest_refactor_cleanup'), ('core', '0012_json_field'), ('core', '0013_unknown_language'), ('core', '0014_httptikaresource'), ('core', '0015_pipeline_processors'), ('core', '0016_extensions'), ('core', '0017_dataset_is_latest'), ('core', '0018_extructresource'), ('core', '0019_dynamic_extraction'), ('core', '0020_dynamic_extraction_data'), ('core', '0021_secure_dynamic_extraction'), ('core', '0022_anatomy_tool'), ('core', '0023_thumbnails_update'), ('core', '0024_pdf_thumbnails'), ('core', '0025_delete_old_resources'), ('core', '0026_alter_objectiveproperty_property'), ('core', '0027_query_annotations'), ('core', '0028_rename_is_addition'), ('core', '0029_matomo'), ('core', '0030_hanze'), ('core', '0031_publisher_year'), ('core', '0032_remove_screenshots'), ('core', '0033_deleted_at_extensions'), ('core', '0034_dataset_version_order'), ('core', '0035_dataset_version_simplification'), ('core', '0036_han_oaipmh'), ('core', '0037_hva_source'), ('core', '0038_hku_source'), ('core', '0039_greeni_source'), ('core', '0040_buas_source'), ('core', '0041_disciplines_and_studies'), ('core', '0042_educational_levels'), ('core', '0043_site_indices'), ('core', '0044_hanze_refactor'), ('core', '0045_remove_extract_mappings'), ('core', '0046_edurep_jsonsearch'), ('core', '0047_publinova_products'), ('core', '0048_alter_harvestsource_repository'), ('core', '0049_alter_harvestsource_repository'), ('core', '0050_remove_deprecated_resources'), ('core', '0051_delete_core_legacy')]

    initial = True

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.CharField(db_index=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'queries',
            },
        ),
        migrations.CreateModel(
            name='QueryRanking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subquery', models.CharField(db_index=True, max_length=255)),
                ('version', models.CharField(default=core.models.search.query.default_version, editable=False, max_length=50)),
                ('ranking', models.JSONField(default=dict)),
                ('is_approved', models.BooleanField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('query', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.query')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='query',
            name='users',
            field=models.ManyToManyField(through='core.QueryRanking', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='MatomoVisitsResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
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
                ('since', models.DateTimeField()),
                ('retainer_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

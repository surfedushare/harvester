# Generated by Django 4.2.13 on 2024-07-10 18:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_remove_deprecated_resources'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='dataset_version',
        ),
        migrations.RemoveField(
            model_name='datasetversion',
            name='dataset',
        ),
        migrations.RemoveField(
            model_name='document',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='document',
            name='dataset_version',
        ),
        migrations.RemoveField(
            model_name='document',
            name='extension',
        ),
        migrations.RemoveField(
            model_name='elasticindex',
            name='dataset_version',
        ),
        migrations.RemoveField(
            model_name='elasticindex',
            name='site',
        ),
        migrations.RemoveField(
            model_name='extension',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='extension',
            name='dataset_version',
        ),
        migrations.RemoveField(
            model_name='extructresource',
            name='retainer_type',
        ),
        migrations.RemoveField(
            model_name='harvest',
            name='dataset',
        ),
        migrations.RemoveField(
            model_name='harvest',
            name='source',
        ),
        migrations.RemoveField(
            model_name='harvestsource',
            name='datasets',
        ),
        migrations.RemoveField(
            model_name='httptikaresource',
            name='retainer_type',
        ),
        migrations.RemoveField(
            model_name='pdfthumbnailresource',
            name='retainer_type',
        ),
        migrations.RemoveField(
            model_name='processresult',
            name='batch',
        ),
        migrations.RemoveField(
            model_name='processresult',
            name='document',
        ),
        migrations.RemoveField(
            model_name='processresult',
            name='result_type',
        ),
        migrations.RemoveField(
            model_name='youtubethumbnailresource',
            name='retainer_type',
        ),
        migrations.DeleteModel(
            name='Batch',
        ),
        migrations.DeleteModel(
            name='Collection',
        ),
        migrations.DeleteModel(
            name='Dataset',
        ),
        migrations.DeleteModel(
            name='DatasetVersion',
        ),
        migrations.DeleteModel(
            name='Document',
        ),
        migrations.DeleteModel(
            name='ElasticIndex',
        ),
        migrations.DeleteModel(
            name='Extension',
        ),
        migrations.DeleteModel(
            name='ExtructResource',
        ),
        migrations.DeleteModel(
            name='Harvest',
        ),
        migrations.DeleteModel(
            name='HarvestSource',
        ),
        migrations.DeleteModel(
            name='HttpTikaResource',
        ),
        migrations.DeleteModel(
            name='PdfThumbnailResource',
        ),
        migrations.DeleteModel(
            name='ProcessResult',
        ),
        migrations.DeleteModel(
            name='YoutubeThumbnailResource',
        ),
    ]
# Generated by Django 3.2.3 on 2021-06-03 17:10

from django.db import migrations, models


def thirty_days_default():
    return {"days": 30}


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_harvest_refactor_cleanup'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='schema',
        ),
        migrations.RemoveField(
            model_name='dataset',
            name='schema',
        ),
        migrations.RemoveField(
            model_name='document',
            name='schema',
        ),
        migrations.AlterField(
            model_name='chromescreenshotresource',
            name='command',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='properties',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='elasticindex',
            name='configuration',
            field=models.JSONField(blank=True),
        ),
        migrations.AlterField(
            model_name='fileresource',
            name='head',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='fileresource',
            name='request',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='harvestsource',
            name='purge_interval',
            field=models.JSONField(default=thirty_days_default),
        ),
        migrations.AlterField(
            model_name='tikaresource',
            name='command',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='youtubedlresource',
            name='command',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='youtubethumbnailresource',
            name='command',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]

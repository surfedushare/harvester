# Generated by Django 3.2.22 on 2023-11-08 16:04

import datagrowth.configuration.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('files', '0003_youtube_api_resource'),
    ]

    operations = [
        migrations.AddField(
            model_name='filedocument',
            name='redirects',
            field=models.CharField(choices=[('exclusive_permanent', 'Exclusively permanent redirects'), ('temporary', 'At least one temporary redirect'), ('no', 'No redirects')], default='no', max_length=50),
        ),
        migrations.AddField(
            model_name='filedocument',
            name='status_code',
            field=models.SmallIntegerField(default=-1),
        ),
        migrations.CreateModel(
            name='CheckURLResource',
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
    ]

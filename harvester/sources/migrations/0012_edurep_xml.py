# Generated by Django 3.2.20 on 2023-10-23 09:10

import datagrowth.configuration.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('sources', '0011_harvest_sources'),
    ]

    operations = [
        migrations.CreateModel(
            name='EdurepOAIPMH',
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
                ('is_extracted', models.BooleanField(default=False)),
                ('retainer_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.contenttype')),
            ],
        ),
    ]
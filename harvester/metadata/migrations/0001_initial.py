# Generated by Django 3.2.8 on 2021-12-30 13:14

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MetadataTranslation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nl', models.CharField(max_length=255, verbose_name='Dutch')),
                ('en', models.CharField(blank=True, max_length=255, verbose_name='English')),
                ('is_fuzzy', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='MetadataField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_hidden', models.BooleanField(default=False)),
                ('is_manual', models.BooleanField(default=False)),
                ('english_as_dutch', models.BooleanField(default=False)),
                ('translation', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='metadata.metadatatranslation')),
            ],
        ),
        migrations.CreateModel(
            name='MetadataValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, default=None, null=True)),
                ('value', models.CharField(max_length=255)),
                ('frequency', models.PositiveIntegerField(default=0)),
                ('is_manual', models.BooleanField(default=False)),
                ('is_hidden', models.BooleanField(default=False)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='metadata.metadatafield')),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='metadata.metadatavalue')),
                ('translation', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='metadata.metadatatranslation')),
            ],
            options={
                'unique_together': {('field', 'value')},
            },
        ),
    ]

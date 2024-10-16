# Generated by Django 4.2.13 on 2024-07-12 09:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('files', '0007_index_json_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='httptikaresource',
            name='retainer_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='pdfthumbnailresource',
            name='retainer_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='youtubethumbnailresource',
            name='retainer_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.DeleteModel(
            name='ExtructResource',
        ),
    ]

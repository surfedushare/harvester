# Generated by Django 3.2.4 on 2021-09-30 12:44

from django.db import migrations, models
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_anatomy_tool'),
    ]

    operations = [
        migrations.AddField(
            model_name='youtubethumbnailresource',
            name='preview',
            field=versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to='core/previews/youtube'),
        ),
    ]

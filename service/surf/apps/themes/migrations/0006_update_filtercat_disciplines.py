# Generated by Django 2.0.13 on 2019-11-04 16:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('filters', '0012_auto_20191112_0918'),
        ('themes', '0005_auto_20190830_0813'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='theme',
            name='disciplines',
        ),
        migrations.RemoveField(
            model_name='theme',
            name='filter_category_item',
        ),
        migrations.RenameField(
            model_name='theme',
            old_name='mptt_disciplines',
            new_name='disciplines',
        ),
        migrations.RenameField(
            model_name='theme',
            old_name='mptt_filter_category_item',
            new_name='filter_category_item',
        ),
    ]

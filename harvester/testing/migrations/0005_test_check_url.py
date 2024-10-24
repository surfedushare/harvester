# Generated by Django 4.2.11 on 2024-05-21 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testing', '0004_django_update'),
    ]

    operations = [
        migrations.AddField(
            model_name='testdocument',
            name='redirects',
            field=models.CharField(choices=[('exclusive_permanent', 'Exclusively permanent redirects'), ('temporary', 'At least one temporary redirect'), ('no', 'No redirects')], default='no', max_length=50),
        ),
        migrations.AddField(
            model_name='testdocument',
            name='status_code',
            field=models.SmallIntegerField(default=-1),
        ),
    ]

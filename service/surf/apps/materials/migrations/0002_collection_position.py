# Generated by Django 2.2.13 on 2020-12-17 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materials', '0001_squashed_0028_collectionmaterial_position'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='position',
            field=models.IntegerField(default=0),
        ),
    ]

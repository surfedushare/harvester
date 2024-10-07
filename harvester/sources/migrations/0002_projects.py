# Generated by Django 4.2.15 on 2024-09-25 11:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sources', '0001_new_harvester'),
    ]

    operations = [
        migrations.AlterField(
            model_name='harvestentity',
            name='type',
            field=models.CharField(choices=[('products', 'Product'), ('files', 'File'), ('projects', 'Project'), ('testing', 'Test')], db_index=True, max_length=50),
        ),
    ]
# Generated by Django 3.2.16 on 2023-07-14 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_alter_harvestsource_repository'),
    ]

    operations = [
        migrations.AlterField(
            model_name='harvestsource',
            name='repository',
            field=models.CharField(choices=[('anatomy_tool.AnatomyToolOAIPMH', 'Anatomy_tool'), ('sources.BuasPureResource', 'Buas'), ('edurep.EdurepOAIPMH', 'Edurep'), ('sources.EdurepJsonSearchResource', 'Edurep_jsonsearch'), ('sources.GreeniOAIPMHResource', 'Greeni'), ('sources.HanOAIPMHResource', 'Han'), ('sources.HanzeResearchObjectResource', 'Hanze'), ('sources.HkuMetadataResource', 'Hku'), ('sources.HvaPureResource', 'Hva'), ('sources.PublinovaMetadataResource', 'Publinova'), ('sources.SaxionOAIPMHResource', 'Saxion'), ('sharekit.SharekitMetadataHarvest', 'Sharekit')], max_length=50),
        ),
    ]
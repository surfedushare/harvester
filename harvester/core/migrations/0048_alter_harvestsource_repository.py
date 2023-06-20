# Generated by Django 3.2.16 on 2023-06-20 16:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_publinova_products'),
    ]

    operations = [
        migrations.AlterField(
            model_name='harvestsource',
            name='repository',
            field=models.CharField(choices=[('anatomy_tool.AnatomyToolOAIPMH', 'Anatomy_tool'), ('sources.BuasPureResource', 'Buas'), ('edurep.EdurepOAIPMH', 'Edurep'), ('sources.EdurepJsonSearchResource', 'Edurep_jsonsearch'), ('sources.GreeniOAIPMHResource', 'Greeni'), ('sources.HanOAIPMHResource', 'Han'), ('sources.HanzeResearchObjectResource', 'Hanze'), ('sources.HkuMetadataResource', 'Hku'), ('sources.HvaPureResource', 'Hva'), ('sources.PublinovaMetadataResource', 'Publinova'), ('sharekit.SharekitMetadataHarvest', 'Sharekit')], max_length=50),
        ),
    ]

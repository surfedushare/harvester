from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_buas_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='objectiveproperty',
            name='property',
            field=models.CharField(choices=[('aggregation_level', 'aggregation_level'), ('analysis_allowed', 'analysis_allowed'), ('authors', 'authors'), ('copyright', 'copyright'), ('copyright_description', 'copyright_description'), ('description', 'description'), ('doi', 'doi'), ('external_id', 'external_id'), ('files', 'files'), ('from_youtube', 'from_youtube'), ('has_parts', 'has_parts'), ('ideas', 'ideas'), ('is_part_of', 'is_part_of'), ('is_restricted', 'is_restricted'), ('keywords', 'keywords'), ('language', 'language'), ('learning_material_disciplines', 'learning_material_disciplines'), ('lom_educational_levels', 'lom_educational_levels'), ('lowest_educational_level', 'lowest_educational_level'), ('material_types', 'material_types'), ('mime_type', 'mime_type'), ('parties', 'parties'), ('publisher_date', 'publisher_date'), ('publisher_year', 'publisher_year'), ('publishers', 'publishers'), ('research_object_type', 'research_object_type'), ('research_themes', 'research_themes'), ('state', 'state'), ('studies', 'studies'), ('technical_type', 'technical_type'), ('title', 'title'), ('url', 'url')], max_length=50),
        ),
    ]

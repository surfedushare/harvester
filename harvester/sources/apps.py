from django.apps import AppConfig
from django.utils.functional import cached_property


class SourcesConfig(AppConfig):

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sources'

    @cached_property
    def staging_providers_by_source(self) -> dict[str, list[str]]:
        from sources.models import HarvestSource
        return {
            source.name: source.staging_providers
            for source in HarvestSource.objects.all()
        }

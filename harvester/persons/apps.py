from django.conf import settings
from django.apps import AppConfig

from search_client.serializers.persons import Person, Researcher
from core.constants import Platforms


class PersonsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'persons'
    document_model = 'PersonDocument'

    @property
    def result_serializer(self):
        """
        Long term we want to use the (Pydantic based) search_client serializers in views directly.
        Until this is possible we return the Django Rest Framework serializers here.
        Notice that validation and input transformation is already being done by the "result_transformer" below.
        The "result_transformer" is already a search_client serializer
        """
        from persons.views.serializers import PersonSerializer, ResearcherSerializer
        if settings.PLATFORM in [Platforms.EDUSOURCES, Platforms.MBODATA]:
            return PersonSerializer
        elif settings.PLATFORM is Platforms.PUBLINOVA:
            return ResearcherSerializer
        else:
            raise AssertionError("PersonsConfig expected application to use different PLATFORM value.")

    @property
    def result_transformer(self):
        """
        Until our views support Pydantic models for serialization, the search_client serializers are only used for
        transformations and validation. Although validations shouldn't ever fail, because we load internal data.
        """
        if settings.PLATFORM in [Platforms.EDUSOURCES, Platforms.MBODATA]:
            return Person
        elif settings.PLATFORM is Platforms.PUBLINOVA:
            return Researcher
        else:
            raise AssertionError("PersonsConfig expected application to use different PLATFORM value.")

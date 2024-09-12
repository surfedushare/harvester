from django.conf import settings
from django.apps import AppConfig

from search_client.constants import Platforms
from search_client.serializers import LearningMaterial, ResearchProduct


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    document_model = 'ProductDocument'

    @property
    def result_serializer(self):
        """
        Long term we want to use the (Pydantic based) search_client serializers in views directly.
        Until this is possible we return the Django Rest Framework serializers here.
        Notice that validation and input transformation is already being done by the "result_transformer" below.
        The "result_transformer" is already a search_client serializer
        """
        from products.views.serializers import SimpleLearningMaterialResultSerializer, ResearchProductResultSerializer
        if settings.PLATFORM is Platforms.EDUSOURCES:
            return SimpleLearningMaterialResultSerializer
        elif settings.PLATFORM is Platforms.PUBLINOVA:
            return ResearchProductResultSerializer
        else:
            raise AssertionError("ProductsConfig expected application to use different PLATFORM value.")

    @property
    def result_transformer(self):
        """
        Until our views support Pydantic models for serialization, the search_client serializers are only used for
        transformations and validation. Although validations shouldn't ever fail, because we load internal data.
        """
        if settings.PLATFORM is Platforms.EDUSOURCES:
            return LearningMaterial
        elif settings.PLATFORM is Platforms.PUBLINOVA:
            return ResearchProduct
        else:
            raise AssertionError("ProductsConfig expected application to use different PLATFORM value.")

from django.conf import settings
from django.apps import AppConfig

from search_client.constants import Platforms


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'
    document_model = 'ProductDocument'

    @property
    def result_serializer(self):
        from products.views.serializers import SimpleLearningMaterialResultSerializer, ResearchProductResultSerializer
        if settings.PLATFORM is Platforms.EDUSOURCES:
            return SimpleLearningMaterialResultSerializer
        elif settings.PLATFORM is Platforms.PUBLINOVA:
            return ResearchProductResultSerializer
        else:
            raise AssertionError("ProductsConfig expected application to use different PLATFORM value.")

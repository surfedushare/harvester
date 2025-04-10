from django.apps import AppConfig

from search_client.serializers import Organization


class OrganizationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organizations'
    document_model = 'OrganizationDocument'

    @property
    def result_serializer(self):
        """
        Long term we want to use the (Pydantic based) search_client serializers in views directly.
        Until this is possible we return the Django Rest Framework serializers here.
        Notice that validation and input transformation is already being done by the "result_transformer" below.
        The "result_transformer" is already a Pydantic serializer
        """
        from organizations.views.serializers import OrganizationSerializer
        return OrganizationSerializer

    @property
    def result_transformer(self):
        """
        Until our views support Pydantic models for serialization, the Pydantic serializers are only used for
        transformations and validation. Although validations shouldn't ever fail, because we load internal data.
        """
        return Organization

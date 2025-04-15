from django.apps import AppConfig

from search_client.serializers import File


class FilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'files'
    document_model = 'FileDocument'

    @property
    def result_transformer(self):
        """
        Until our views support Pydantic models for serialization, the search_client serializers are only used for
        transformations and validation. Although validations shouldn't ever fail, because we load internal data.
        """
        return File

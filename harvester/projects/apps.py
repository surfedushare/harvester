from django.apps import AppConfig

from search_client.serializers import Project


class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'projects'
    document_model = 'ProjectDocument'

    @property
    def result_serializer(self):
        """
        Long term we want to use the (Pydantic based) search_client serializers in views directly.
        Until this is possible we return the Django Rest Framework serializers here.
        Notice that validation and input transformation is already being done by the "result_transformer" below.
        The "result_transformer" is already a search_client serializer
        """
        from projects.views.serializers import ProjectSerializer
        return ProjectSerializer

    @property
    def result_transformer(self):
        """
        Until our views support Pydantic models for serialization, the search_client serializers are only used for
        transformations and validation. Although validations shouldn't ever fail, because we load internal data.
        """
        return Project

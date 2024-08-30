import json

from django.apps import apps
from django.core.management.base import BaseCommand
from rest_framework.exceptions import ValidationError
from tqdm import tqdm
from pydantic import ValidationError as PydanticValidationError

from products.models import DatasetVersion, ProductDocument


class Command(BaseCommand):
    """
    A command that checks whether data from a products DatasetVersion will serialize without errors.
    """

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('-dv', '--dataset-version-id', type=int)

    def handle(self, *args, **options):
        dataset_version_id = options['dataset_version_id']
        dataset_version = DatasetVersion.objects.get(id=dataset_version_id)

        products_app = apps.get_app_config("products")
        serializer_class = products_app.result_serializer
        transformer_class = products_app.result_transformer

        documents = dataset_version.documents.filter(state=ProductDocument.States.ACTIVE)
        for document in tqdm(documents.iterator(), total=documents.count()):
            data = document.to_data()
            if not data:
                self.stdout.write(f"Missing data for: {document.identity}")
                continue
            try:
                transformed_model = transformer_class(**data)
            except PydanticValidationError as exc:
                self.stdout.write(json.dumps(data, indent=4))
                raise exc
            transformed_data = transformed_model.model_dump(mode="json")
            serializer = serializer_class(data=transformed_data)
            try:
                serializer.is_valid(raise_exception=True)
            except ValidationError as exc:
                self.stdout.write(json.dumps(transformed_data, indent=4))
                raise exc

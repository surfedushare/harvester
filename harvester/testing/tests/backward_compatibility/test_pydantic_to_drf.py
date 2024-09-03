import json

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from search_client.constants import Platforms
from search_client.test.factories import generate_nl_material, generate_nl_product, generate_material, generate_product
from search_client.serializers.products import LearningMaterial, ResearchProduct

from products.views.serializers import SimpleLearningMaterialResultSerializer, ResearchProductResultSerializer


class TestPydanticToDRFConversion(TestCase):

    factories = {
        Platforms.EDUSOURCES: [generate_nl_material, generate_material],
        Platforms.PUBLINOVA: [generate_nl_product, generate_product]
    }

    def test_edusources(self):
        for factory in self.factories[Platforms.EDUSOURCES]:
            for topic in ["math", "biology"]:
                data = factory(topic=topic)
                learning_material = LearningMaterial(**data)
                learning_material_json = learning_material.model_dump_json()
                untyped_learning_material = json.loads(learning_material_json)
                serializer = SimpleLearningMaterialResultSerializer(data=untyped_learning_material)
                try:
                    serializer.is_valid(raise_exception=True)
                except ValidationError as exc:
                    self.fail(
                        f"SimpleLearningMaterialResultSerializer raised validation error "
                        f"with {topic} using factory {factory.__name__}: {exc}"
                    )

    def test_publinova(self):
        for factory in self.factories[Platforms.PUBLINOVA]:
            for topic in ["math", "biology"]:
                data = generate_nl_material(topic=topic)
                research_product = ResearchProduct(**data)
                research_product_json = research_product.model_dump_json()
                untyped_research_product = json.loads(research_product_json)
                serializer = ResearchProductResultSerializer(data=untyped_research_product)
                try:
                    serializer.is_valid(raise_exception=True)
                except ValidationError as exc:
                    self.fail(
                        f"ResearchProductResultSerializer raised validation error "
                        f"with {topic} using factory {factory.__name__}: {exc}"
                    )

import json

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from search_client.test.factories import generate_nl_material
from search_client.serializers.products import LearningMaterial, ResearchProduct

from products.views.serializers import SimpleLearningMaterialResultSerializer, ResearchProductResultSerializer


class TestPydanticToDRFConversion(TestCase):

    def test_learning_material_math(self):
        data = generate_nl_material(topic="math")
        learning_material = LearningMaterial(**data)
        learning_material_json = learning_material.model_dump_json()
        untyped_learning_material = json.loads(learning_material_json)
        serializer = SimpleLearningMaterialResultSerializer(data=untyped_learning_material)
        try:
            serializer.is_valid()
        except ValidationError as exc:
            self.fail(f"SimpleLearningMaterialResultSerializer raised validation error: {exc}")

    def test_research_product_math(self):
        data = generate_nl_material(topic="math")
        research_product = ResearchProduct(**data)
        research_product_json = research_product.model_dump_json()
        untyped_research_product = json.loads(research_product_json)
        serializer = ResearchProductResultSerializer(data=untyped_research_product)
        try:
            serializer.is_valid()
        except ValidationError as exc:
            self.fail(f"ResearchProductResultSerializer raised validation error: {exc}")

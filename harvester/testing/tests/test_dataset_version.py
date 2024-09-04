from decimal import Decimal

from django.test import TestCase

from testing.models import Dataset, DatasetVersion


class TestDatasetVersion(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.dataset = Dataset(name="test")

    def test_get_numeric_version(self):
        dataset_version = DatasetVersion(dataset=self.dataset, version="0.0.1")
        self.assertEqual(dataset_version.get_numeric_version(), (Decimal("0.0"), 1,))
        dataset_version = DatasetVersion(dataset=self.dataset, version="1.99.99")
        self.assertEqual(dataset_version.get_numeric_version(), (Decimal("1.99"), 99,))

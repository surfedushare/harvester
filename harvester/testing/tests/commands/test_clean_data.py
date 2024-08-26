from unittest.mock import patch
from datetime import datetime, timedelta

from django.test import TestCase
from django.core.management import call_command
from django.utils.timezone import make_aware

from search.models import OpenSearchIndex
from files.models import FileDocument, HttpTikaResource, DatasetVersion, Set, Dataset
from files.sources.sharekit import SEQUENCE_PROPERTIES
from files.tests.factories.tika import HttpTikaResourceFactory
from testing.utils.mocks import get_search_client_mock
from testing.utils.factories import create_datatype_models
from testing.utils.generators import seed_generator


def create_version_copy(dataset_version, version, created_at):
    version_copy = dataset_version.dataset.copy_dataset_version(dataset_version)
    version_copy.is_current = False
    version_copy.version = version
    version_copy.created_at = created_at
    version_copy.index = OpenSearchIndex.build("products", version_copy.dataset.name, version_copy.version)
    version_copy.index.save()
    version_copy.save()
    return version_copy


def set_tika_pipeline(dataset_version):
    documents = []
    for doc in dataset_version.documents.all():
        tika_resource = HttpTikaResourceFactory.create(
            created_at=dataset_version.created_at,
            modified_at=dataset_version.created_at,
            purge_at=dataset_version.created_at
        )
        doc.pipeline = {
            "tika": {
                "success": tika_resource.success,
                "resource": "{}.{}".format(tika_resource._meta.app_label, tika_resource._meta.model_name),
                "id": tika_resource.id
            }
        }
        documents.append(doc)
    FileDocument.objects.bulk_update(documents, ["pipeline"])


def update_generated_version(dataset_version: DatasetVersion, version=None):
    dataset_version.index = OpenSearchIndex.build("products", dataset_version.dataset.name, dataset_version.version)
    dataset_version.index.save()
    if version:
        dataset_version.version = version
        dataset_version.is_current = False
    dataset_version.save()
    set_tika_pipeline(dataset_version)
    active_version_copy = create_version_copy(dataset_version, dataset_version.version, dataset_version.created_at)
    set_tika_pipeline(active_version_copy)


class TestCleanData(TestCase):

    search_client = get_search_client_mock(has_history=True)

    def setUp(self):
        super().setUp()

        file_seeds = list(seed_generator("sharekit", 10, app_label="files", sequence_properties=SEQUENCE_PROPERTIES))

        active_dataset, active_dataset_version, active_sets, active_documents = create_datatype_models(
            "files", ["test"], file_seeds[0:5], 5
        )
        update_generated_version(active_dataset_version)
        created_time = make_aware(datetime.now())
        for version_number in range(0, 29, 7):
            created_time -= timedelta(days=version_number)
            version = f"0.0.{28 - version_number}"
            for _ in range(0, 2):
                dataset_version_copy = create_version_copy(active_dataset_version, version, created_time)
                set_tika_pipeline(dataset_version_copy)

        inactive_dataset, inactive_dataset_version, inactive_sets, inactive_documents = create_datatype_models(
            "files", ["test"], file_seeds[5:], 5
        )
        update_generated_version(inactive_dataset_version, version="0.0.28")
        created_time = make_aware(datetime.now())
        for version_number in range(21, 43, 7):
            created_time -= timedelta(days=version_number)
            version = f"0.0.{42 - version_number}"
            for _ in range(0, 2):
                dataset_version_copy = create_version_copy(inactive_dataset_version, version, created_time)
                set_tika_pipeline(dataset_version_copy)

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    def test_clean_data(self, get_search_client):
        get_search_client.reset_mock()
        call_command("clean_data")
        # Assert which data remains
        self.assertEqual(Dataset.objects.count(), 2, "clean_data should never delete Datasets")
        self.assertEqual(DatasetVersion.objects.filter(is_current=False).count(), 7,
                         "Per dataset only younger than DATA_RETENTION_PURGE_AFTER of non-currents should remain "
                         "outside of the DATA_RETENTION_KEEP_VERSIONS amount")
        self.assertEqual(
            DatasetVersion.objects.filter(is_current=True).count(), 1,
            "Expected one is_current dataset version to exist at all times"
        )
        self.assertEqual(OpenSearchIndex.objects.count(), 8, "Expected one index per dataset version")
        self.assertEqual(Set.objects.count(), 8, "Expected one collection per dataset version")
        self.assertEqual(FileDocument.objects.count(), 40, "Expected five documents per collection")
        self.assertEqual(HttpTikaResource.objects.count(), 40, "Expected one HttpTikaResource per Document")
        # Check if indices were removed properly as well
        self.assertEqual(get_search_client.call_count, 14, "Not sure why there are two calls per removed index")
        self.assertEqual(
            self.search_client.indices.exists.call_count, 9,
            "Expected 0.0.0, 0.0.7 and 0.0.14 to be checked for deletion when last DatasetVersions instance was cleaned"
        )
        self.assertEqual(
            self.search_client.indices.delete.call_count, 9,
            "Expected 0.0.0, 0.0.7 and 0.0.14 to be deleted when last DatasetVersions instance was cleaned"
        )

    def test_clean_data_duplicated_resources(self):
        # We'll add old Resources to new Documents and make sure these resources do not get deleted
        oldest_version = DatasetVersion.objects.last()  # will get removed
        newest_version = DatasetVersion.objects.first()  # will remain
        old_tika_ids = []
        new_tika_ids = []
        for old_doc, new_doc in zip(oldest_version.documents.all(), newest_version.documents.all()):
            old_tika_ids.append(old_doc.pipeline["tika"]["id"])
            new_tika_ids.append(new_doc.pipeline["tika"]["id"])
            new_doc.properties = old_doc.properties
            new_doc.save()
        self.assertEqual(HttpTikaResource.objects.filter(id__in=old_tika_ids).count(), len(old_tika_ids),
                         "Old HttpTikaResource should remain, because new Documents use them")
        self.assertEqual(HttpTikaResource.objects.filter(id__in=new_tika_ids).count(), len(new_tika_ids),
                         "New HttpTikaResource without Document should remain, because they are new")

    @patch("search.models.index.get_opensearch_client", return_value=search_client)
    def test_clean_data_missing_resources(self, get_search_client):
        # We'll remove all resources. This should not interfere with deletion of other data
        HttpTikaResource.objects.all().delete()
        get_search_client.reset_mock()
        call_command("clean_data")
        # Assert which data remains
        self.assertEqual(Dataset.objects.count(), 2, "clean_data should never delete Datasets")
        self.assertEqual(DatasetVersion.objects.filter(is_current=False).count(), 7,
                         "Per dataset only younger than DATA_RETENTION_PURGE_AFTER of non-currents should remain "
                         "outside of the DATA_RETENTION_KEEP_VERSIONS amount")
        self.assertEqual(
            DatasetVersion.objects.filter(is_current=True).count(), 1,
            "Expected one is_current dataset version to exist at all times"
        )
        self.assertEqual(OpenSearchIndex.objects.count(), 8, "Expected one indices per dataset version")
        self.assertEqual(Set.objects.count(), 8, "Expected one collection per dataset version")
        self.assertEqual(FileDocument.objects.count(), 40, "Expected five documents per collection")
        self.assertEqual(HttpTikaResource.objects.count(), 0)
        # Check if indices were removed properly as well
        self.assertEqual(get_search_client.call_count, 14, "Not sure why there are two calls per removed index")
        self.assertEqual(self.search_client.indices.exists.call_count, 9,
            "Expected 0.0.0, 0.0.7 and 0.0.14 to be checked for deletion when last DatasetVersions instance was cleaned"
        )
        self.assertEqual(
            self.search_client.indices.delete.call_count, 9,
            "Expected 0.0.0, 0.0.7 and 0.0.14 to be deleted when last DatasetVersions instance was cleaned"
        )

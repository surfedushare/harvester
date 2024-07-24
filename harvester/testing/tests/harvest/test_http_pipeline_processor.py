from unittest.mock import MagicMock, patch

from django.test import TestCase
from celery.canvas import Signature

from core.processors import HttpPipelineProcessor
from files.models import Batch, ProcessResult, HttpTikaResource
from files.sources.sharekit import SEQUENCE_PROPERTIES
from files.tests.factories.tika import HttpTikaResourceFactory
from testing.utils.factories import create_datatype_models
from testing.utils.generators import seed_generator


chord_mock_result = MagicMock()


class TestHttpPipelineProcessor(TestCase):

    @classmethod
    def setUpTestData(cls):
        file_seeds = list(seed_generator("sharekit", 10, app_label="files", sequence_properties=SEQUENCE_PROPERTIES))
        active_dataset, active_dataset_version, active_sets, active_documents = create_datatype_models(
            "files", ["test"], file_seeds[0:5], 5
        )
        cls.set = active_sets[0]
        for ix, seed in enumerate(file_seeds[1:]):
            # This loop never sees the first seed and creates an error Tika instance for the second seed.
            if not ix:
                status = 500
            else:
                status = 200
            HttpTikaResourceFactory.create(url=seed["url"], status=status)

    @patch("files.models.resources.metadata.HttpTikaResource._send")
    def test_synchronous_tika_pipeline(self, send_mock):
        resource = "files.httptikaresource"
        processor = HttpPipelineProcessor({
            "pipeline_app_label": "files",
            "pipeline_models": {
                "document": "FileDocument",
                "process_result": "ProcessResult",
                "batch": "Batch"
            },
            "pipeline_phase": "tika",
            "batch_size": 2,
            "asynchronous": False,
            "retrieve_data": {
                "tika_return_type": "text",
                "resource": resource,
                "method": "put",
                "args": ["$.url"],
                "kwargs": {},
            },
            "contribute_data": {
                "to_property": "derivatives/tika",
                "objective": {
                    "@": "$.0",
                    "text": "$.X-TIKA:content"
                }
            }
        })

        processor(self.set.documents.all())
        self.assertEqual(
            Batch.objects.count(), 3,
            "Expected batches to remain after use, because deleting in async environment leads to race conditions"
        )
        self.assertEqual(ProcessResult.objects.count(), 0, "Expected ProcessResults to get deleted after use")
        self.assertEqual(self.set.documents.count(), 5)
        for document in self.set.documents.all():
            self.assertIn("tika", document.pipeline)
            tika_pipeline = document.pipeline["tika"]
            self.assertEqual(tika_pipeline["resource"], "files.httptikaresource")
            self.assertIsInstance(tika_pipeline["id"], int)
            self.assertIsInstance(tika_pipeline["success"], bool)
            tika_resource = HttpTikaResource.objects.get(id=tika_pipeline["id"])
            if tika_resource.status == 200:  # Incomplete testing Tika responses are 204
                self.assertIsInstance(
                    document.derivatives["tika"]["text"], str,
                    "Expected text to be extracted from Tika responses if they succeed"
                )
        self.assertEqual(send_mock.call_count, 2, "Expected one erroneous resource to retry and one new resource")

    @patch("core.processors.pipeline.base.chord", return_value=chord_mock_result)
    def test_asynchronous_pipeline(self, chord_mock):
        """
        This test only asserts if Celery is used as expected.
        See synchronous test for actual result testing.
        """
        resource = "files.httptikaresource"
        processor = HttpPipelineProcessor({
            "pipeline_app_label": "files",
            "pipeline_phase": "tika",
            "pipeline_models": {
                "document": "FileDocument",
                "process_result": "ProcessResult",
                "batch": "Batch"
            },
            "batch_size": 2,
            "asynchronous": True,
            "retrieve_data": {
                "tika_return_type": "text",
                "resource": resource,
                "method": "put",
                "args": ["$.url"],
                "kwargs": {},
            },
            "contribute_data": {
                "objective": {
                    "@": "$.0",
                    "text": "$.X-TIKA:content"
                }
            }
        })
        task = processor(self.set.documents.all())
        task.get()
        self.assertEqual(chord_mock.call_count, 1)
        chord_call = chord_mock.call_args_list[0]
        chord_call_args = chord_call.args
        self.assertEqual(len(chord_call_args), 1)
        for ix, signature in enumerate(chord_call_args[0]):
            self.assertIsInstance(signature, Signature)
            self.assertEqual(signature.name, "pipeline_process_and_merge")
            for arg in signature.args:
                self.assertIsInstance(arg, int, "Expected a batch id as an argument in the signature")
            self.assertIn("config", signature.kwargs)
        self.assertEqual(chord_mock_result.call_count, 1)
        chord_result_call = chord_mock_result.call_args_list[0]
        chord_result_call_args = chord_result_call.args
        self.assertEqual(len(chord_result_call_args), 1)
        finish_signature = chord_result_call_args[0]
        self.assertIsInstance(finish_signature, Signature)
        self.assertEqual(finish_signature.name, "pipeline_full_merge")
        self.assertEqual(finish_signature.args, ("HttpPipelineProcessor",))
        self.assertIn("config", finish_signature.kwargs)

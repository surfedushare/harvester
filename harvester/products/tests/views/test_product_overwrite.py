from unittest.mock import patch

from django.test import TestCase
from django.db import DatabaseError
from django.utils.timezone import now
from django.contrib.auth.models import User
from rest_framework import status

from products.models import ProductDocument, Overwrite


class TestProductOverwriteAPI(TestCase):

    fixtures = ["test-product-document"]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="supersurf")
        cls.test_srn = "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e"

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def assert_overwrite(self, overwrite: dict, srn: str):
        expected_keys = {"id", "created_at", "modified_at", "properties"}
        for key in overwrite.keys():
            self.assertIn(key, expected_keys)
        self.assertEqual(overwrite["id"], srn)
        self.assertIsNotNone(overwrite["created_at"])
        self.assertIsNotNone(overwrite["modified_at"])
        self.assertIsInstance(overwrite["properties"], dict)

    def delete_test_overwrite(self, hard: bool = True):
        overwrite = Overwrite.objects.get(id=self.test_srn)
        if hard:
            overwrite.deleted_at = now()  # skips "trash" delete
        overwrite.delete()

    def test_list(self):
        """
        When listing Overwrites a correct pagination response should be returned.
        """
        response = self.client.get("/api/v1/product/overwrite/")
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        expected_keys = {"count", "next", "previous", "results"}
        for key in expected_keys:
            self.assertIn(key, expected_keys)
        self.assertEqual(response_data["count"], 1)
        self.assertIsNone(response_data["next"])
        self.assertIsNone(response_data["previous"])
        self.assertIsInstance(response_data["results"], list)
        self.assertEqual(len(response_data["results"]), 1)
        self.assert_overwrite(response_data["results"][0], "sharekit:edusources:63903863-6c93-4bda-b850-277f3c9ec00e")

    def test_list_deletes(self):
        """
        When listing Overwrites soft deleted Overwrites should not be included in that list
        """
        # We first delete the existing Overwrite to make sure were testing correctly
        self.delete_test_overwrite(hard=False)
        # Request the list
        response = self.client.get("/api/v1/product/overwrite/")
        # Assert structure
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        expected_keys = {"count", "next", "previous", "results"}
        for key in expected_keys:
            self.assertIn(key, expected_keys)
        self.assertEqual(response_data["count"], 0)
        self.assertIsNone(response_data["next"])
        self.assertIsNone(response_data["previous"])
        self.assertIsInstance(response_data["results"], list)
        self.assertEqual(len(response_data["results"]), 0)

    def test_list_empty(self):
        """
        When listing Overwrites, but none exist an empty list should be returned.
        """
        # We first delete the existing Overwrite to make sure were testing correctly
        self.delete_test_overwrite()
        # Request the list
        response = self.client.get("/api/v1/product/overwrite/")
        # Assert structure
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        expected_keys = {"count", "next", "previous", "results"}
        for key in expected_keys:
            self.assertIn(key, expected_keys)
        self.assertEqual(response_data["count"], 0)
        self.assertIsNone(response_data["next"])
        self.assertIsNone(response_data["previous"])
        self.assertIsInstance(response_data["results"], list)
        self.assertEqual(len(response_data["results"]), 0)

    def test_create(self):
        """
        When creating an Overwrite we should be able to set properties like metrics.
        """
        # We first delete the existing Overwrite to make sure were testing correctly
        self.delete_test_overwrite()
        # Put a new Overwrite
        body = {
            "srn": self.test_srn,
            "metrics": {
                "views": 1,
                "star_1": 5,
                "star_2": 4,
                "star_3": 3,
                "star_4": 2,
                "star_5": 1,
            }
        }
        response = self.client.put(f"/api/v1/product/overwrite/{self.test_srn}/", body, content_type="application/json")
        # Assert
        expected_overwrites = {
            "metrics": body["metrics"]
        }
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assert_overwrite(response_data, self.test_srn)
        self.assertEqual(response_data["properties"], expected_overwrites)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertIsNotNone(document.overwrite)
        self.assertEqual(document.overwrite.properties, expected_overwrites)

    def test_create_partial_data(self):
        """
        When creating an Overwrite we should be able to set properties like metrics, without specifying all detail.
        """
        # We first delete the existing Overwrite to make sure were testing correctly
        self.delete_test_overwrite()
        # Put a new Overwrite
        body = {
            "srn": self.test_srn,
            "metrics": {
                "star_5": 1,
            }
        }
        response = self.client.put(f"/api/v1/product/overwrite/{self.test_srn}/", body, content_type="application/json")
        # Assert
        expected_overwrites = {
            "metrics": {
                "views": 0,
                "star_1": 0,
                "star_2": 0,
                "star_3": 0,
                "star_4": 0,
                "star_5": 1,
            }
        }
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assert_overwrite(response_data, self.test_srn)
        self.assertEqual(response_data["properties"], expected_overwrites)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertIsNotNone(document.overwrite)
        self.assertEqual(document.overwrite.properties, expected_overwrites)

    def test_update(self):
        """
        Updating an existing Overwrite with a PUT means that all properties will get overridden.
        There is no merging done for properties.
        """
        datetime_begin_test = now()
        # Put the Override
        body = {
            "srn": self.test_srn,
            "metrics": {
                "views": 100,
                "star_1": 1,
                "star_2": 2,
                "star_3": 3,
                "star_4": 4,
                "star_5": 5,
            }
        }
        response = self.client.put(f"/api/v1/product/overwrite/{self.test_srn}/", body, content_type="application/json")
        # Asserts
        expected_overwrites = {
            "metrics": body["metrics"]
        }
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assert_overwrite(response_data, self.test_srn)
        self.assertEqual(response_data["properties"], expected_overwrites)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertIsNotNone(document.overwrite)
        self.assertEqual(document.overwrite.properties, expected_overwrites)
        self.assertGreater(document.modified_at, datetime_begin_test,
                           "Expected modified_at of document to get updated")

    def test_update_partial_data(self):
        """
        Updating an existing Overwrite with a PUT means that all properties will get overridden
        and defaults are used when properties are missing. There is no merging done for properties.
        """
        datetime_begin_test = now()
        # Put the Override
        body = {
            "srn": self.test_srn,
            "metrics": {
                "views": 100
            }
        }
        response = self.client.put(f"/api/v1/product/overwrite/{self.test_srn}/", body, content_type="application/json")
        # Asserts
        expected_overwrites = {
            "metrics": {
                "views": 100,
                "star_1": 0,
                "star_2": 0,
                "star_3": 0,
                "star_4": 0,
                "star_5": 0,
            }
        }
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assert_overwrite(response_data, self.test_srn)
        self.assertEqual(response_data["properties"], expected_overwrites)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertIsNotNone(document.overwrite)
        self.assertEqual(document.overwrite.properties, expected_overwrites)
        self.assertGreater(document.modified_at, datetime_begin_test,
                           "Expected modified_at of document to get updated")

    def test_update_under_lock(self):
        """
        PUT doesn't support concurrent updates and will fail with a "conflict" error code.
        """
        with patch('django.db.models.query.QuerySet.select_for_update') as mock_lock:
            mock_lock.side_effect = DatabaseError("could not obtain lock")
            response = self.client.put(
                f"/api/v1/product/overwrite/{self.test_srn}/",
                data={
                    "srn": self.test_srn,
                    "metrics": {
                        "views": 100,
                        "star_1": 1,
                        "star_2": 2,
                        "star_3": 3,
                        "star_4": 4,
                        "star_5": 5,
                    }
                },
                content_type="application/json"
            )
        # Asserts
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertIsNotNone(document.overwrite)
        self.assertEqual(document.overwrite.properties, {
            "metrics": {
                "views": 1,
                "star_1": 5,
                "star_2": 4,
                "star_3": 3,
                "star_4": 2,
                "star_5": 1,
            }
        })

    def test_patch_create(self):
        """
        Creating an Overwrite with a PATCH can only occur with a limited set of properties.
        """
        # We first delete the existing Overwrite to make sure were testing correctly
        self.delete_test_overwrite()
        # Patch the Override
        body = {
            "srn": self.test_srn,
            "metrics": {
                "views": 1,
            }
        }
        url = f"/api/v1/product/overwrite/{self.test_srn}/"
        response = self.client.patch(url, body, content_type="application/json")
        # Asserts
        expected_overwrites = {
            "metrics": {
                "views": 1,
                "star_1": 0,
                "star_2": 0,
                "star_3": 0,
                "star_4": 0,
                "star_5": 0,
            }
        }
        self.assertEqual(response.status_code, 201)
        response_data = response.json()
        self.assert_overwrite(response_data, self.test_srn)
        self.assertEqual(response_data["properties"], expected_overwrites)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertIsNotNone(document.overwrite)
        self.assertEqual(document.overwrite.properties, expected_overwrites)

    def test_patch_create_invalid(self):
        """
        Creating an Overwrite with a PATCH can only occur with a limited set of properties.
        """
        # We first delete the existing Overwrite to make sure were testing correctly
        self.delete_test_overwrite()
        # Patch the Override
        body = {
            "srn": self.test_srn,
            "metrics": {
                "views": 1,
                "star_5": 1,
            }
        }
        url = f"/api/v1/product/overwrite/{self.test_srn}/"
        response = self.client.patch(url, body, content_type="application/json")
        # Asserts
        self.assertEqual(response.status_code, 400)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertIsNone(document.overwrite)

    def test_patch_update(self):
        """
        Updating an existing Overwrite with a PATCH means that some properties will get merged.
        """
        datetime_begin_test = now()
        # Patch the Override
        body = {
            "srn": self.test_srn,
            "metrics": {
                "views": 1
            }
        }
        url = f"/api/v1/product/overwrite/{self.test_srn}/"
        response = self.client.patch(url, body, content_type="application/json")
        # Asserts
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assert_overwrite(response_data, self.test_srn)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertIsNotNone(document.overwrite)
        self.assertEqual(document.overwrite.properties, {
            "metrics": {
                "views": 2,
                "star_1": 5,
                "star_2": 4,
                "star_3": 3,
                "star_4": 2,
                "star_5": 1,
            }
        })
        self.assertGreater(document.modified_at, datetime_begin_test,
                           "Expected modified_at of document to get updated")

    def test_patch_update_invalid(self):
        """
        Updating an existing Overwrite with a PATCH can only occur with a limited set of properties per request.
        """
        # Patch the Override
        body = {
            "srn": self.test_srn,
            "metrics": {
                "views": 1,
                "star_1": 1,
            }
        }
        url = f"/api/v1/product/overwrite/{self.test_srn}/"
        response = self.client.patch(url, body, content_type="application/json")
        # Asserts
        self.assertEqual(response.status_code, 400)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertIsNotNone(document.overwrite)
        self.assertEqual(document.overwrite.properties, {
            "metrics": {
                "views": 1,
                "star_1": 5,
                "star_2": 4,
                "star_3": 3,
                "star_4": 2,
                "star_5": 1,
            }
        })

    def test_patch_update_under_lock(self):
        """
        PATCH will support concurrent updates by leveraging nowait=False in the transaction.
        """
        with patch('django.db.models.query.QuerySet.select_for_update') as mock_lock:
            mock_lock.return_value = Overwrite.objects
            response = self.client.patch(
                f"/api/v1/product/overwrite/{self.test_srn}/",
                data={
                    "srn": self.test_srn,
                    "metrics": {
                        "star_1": 1
                    }
                },
                content_type="application/json"
            )
            mock_lock.assert_called_once_with(nowait=False)
        # Asserts of models and responses
        self.assertEqual(response.status_code, 200)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertIsNotNone(document.overwrite)
        self.assertEqual(document.overwrite.properties, {
            "metrics": {
                "views": 1,
                "star_1": 6,
                "star_2": 4,
                "star_3": 3,
                "star_4": 2,
                "star_5": 1,
            }
        })

    def test_delete(self):
        datetime_begin_test = now()
        response = self.client.delete(f"/api/v1/product/overwrite/{self.test_srn}/", content_type="application/json")
        self.assertEqual(response.status_code, 204)
        document = ProductDocument.objects.get(identity=self.test_srn)
        self.assertGreater(document.modified_at, datetime_begin_test,
                           "Expected modified_at of document to get updated")
        overwrite = Overwrite.objects.get(id=self.test_srn)
        self.assertGreater(overwrite.deleted_at, datetime_begin_test)
        # Check whether the deleted extensions are truly not returned by the API
        response = self.client.get(f"/api/v1/product/overwrite/{self.test_srn}/", content_type="application_json")
        self.assertEqual(response.status_code, 404)

    def test_delete_does_not_exist(self):
        response = self.client.delete("/api/v1/product/overwrite/does-not-exist/", content_type="application/json")
        self.assertEqual(response.status_code, 404)

    def test_srn_mismatch(self):
        url = f"/api/v1/product/overwrite/{self.test_srn}/"
        body = {
            "srn": "wrong",
            "metrics": {}
        }
        put_response = self.client.put(url, body, content_type="application/json")
        self.assertEqual(put_response.status_code, 400)
        patch_response = self.client.patch(url, body, content_type="application/json")
        self.assertEqual(patch_response.status_code, 400)


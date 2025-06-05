from django.test import TestCase
from django.db import transaction

from organizations.models import Dataset, DatasetVersion, OrganizationDocument, Set
from organizations.tasks import lookup_organization_parents


class TestOrganizationHierarchy(TestCase):

    fixtures = ["test-organization-document.json"]

    def setUp(self):
        self.dataset = Dataset.objects.get(pk=1)
        self.version = DatasetVersion.objects.get(pk=1)
        self.organization_set = Set.objects.get(pk=1)  # sharekit:nppo set
        self.documents = OrganizationDocument.objects.filter(id__in=self.organization_set.documents.all())

        # Map of SRNs to documents for easier reference in tests
        self.doc_map = {doc.identity: doc for doc in self.documents}

        # Expected organization hierarchy from test data:
        # Hogeschool Utrecht (root)
        # └── Kenniscentrum Sociale Innovatie
        #     └── Toegang tot het Recht

    def test_organization_hierarchy_building(self):
        """
        Test that the organization hierarchy is correctly built and stored in the set's documents
        """
        # Run the task on the organization set
        lookup_organization_parents("organizations", self.organization_set.id)

        # Refresh documents from database
        self.documents = OrganizationDocument.objects.filter(id__in=self.organization_set.documents.all())
        self.doc_map = {doc.identity: doc for doc in self.documents}

        # Test root organization (Hogeschool Utrecht)
        hu_doc = self.doc_map["sharekit:nppo:9bc007df-82c3-4bcb-9b94-1dfd5d77f9ca"]
        self.assertIn("lookup_organization_parents", hu_doc.derivatives)
        self.assertEqual(hu_doc.derivatives["lookup_organization_parents"]["parents"], [])

        self.assertNotIn("is_root", hu_doc.properties, "HALLUCINATION: is_root in properties?")

        # Test middle organization (Kenniscentrum Sociale Innovatie)
        ksi_doc = self.doc_map["sharekit:nppo:66a0079d-c8c2-4bf1-93b9-a2133aa57524"]
        self.assertIn("lookup_organization_parents", ksi_doc.derivatives)
        ksi_parents = ksi_doc.derivatives["lookup_organization_parents"]["parents"]
        self.assertEqual(len(ksi_parents), 1)
        self.assertEqual(ksi_parents[0]["srn"], hu_doc.identity)
        self.assertEqual(ksi_parents[0]["name"], hu_doc.properties["name"])
        self.assertEqual(ksi_parents[0]["ror"], hu_doc.properties["ror"])
        self.assertTrue(ksi_parents[0]["is_root"])

        # Test leaf organization (Toegang tot het Recht)
        ttr_doc = self.doc_map["sharekit:nppo:7c2a6784-4d18-472e-bf5e-f3a61cd66fae"]
        self.assertIn("lookup_organization_parents", ttr_doc.derivatives)
        ttr_parents = ttr_doc.derivatives["lookup_organization_parents"]["parents"]
        self.assertEqual(len(ttr_parents), 2)  # Both KSI and the root parent

        # Verify KSI is in parents with correct data
        ksi_in_parents = next((p for p in ttr_parents if p["srn"] == ksi_doc.identity), None)
        self.assertIsNotNone(ksi_in_parents)
        self.assertEqual(ksi_in_parents["name"], ksi_doc.properties["name"])
        self.assertEqual(ksi_in_parents["ror"], ksi_doc.properties["ror"])
        self.assertFalse(ksi_in_parents["is_root"])  # KSI has HU as parent

        # Verify HU is in parents with correct data (through KSI)
        hu_in_parents = next((p for p in ttr_parents if p["srn"] == hu_doc.identity), None)
        self.assertIsNotNone(hu_in_parents)
        self.assertEqual(hu_in_parents["name"], hu_doc.properties["name"])
        self.assertEqual(hu_in_parents["ror"], hu_doc.properties["ror"])
        self.assertTrue(hu_in_parents["is_root"])

        # Verify inactive parent is not in ancestry (since it"s not in our document set)
        inactive_parent_srn = "sharekit:nppo:6660079d-c8c2-4bf1-93b9-a2133aa57555"
        inactive_in_parents = any(p["srn"] == inactive_parent_srn for p in ttr_parents)
        self.assertFalse(inactive_in_parents)

    def test_task_results(self):
        """
        Test that task results are properly set for all documents in the set and the set itself
        """
        lookup_organization_parents("organizations", self.organization_set.id)

        # Refresh from database
        self.organization_set.refresh_from_db()
        self.documents = OrganizationDocument.objects.filter(id__in=self.organization_set.documents.all())

        # Check set task results
        self.assertIn("lookup_organization_parents", self.organization_set.task_results)
        self.assertTrue(self.organization_set.task_results["lookup_organization_parents"]["success"])

        # Check document task results
        for doc in self.documents:
            self.assertIn("lookup_organization_parents", doc.task_results)
            self.assertTrue(doc.task_results["lookup_organization_parents"]["success"])

    def test_cycle_prevention(self):
        """
        Test that cycles in parent relationships are prevented within the set
        """
        # Create a cycle: A -> B -> C -> A
        with transaction.atomic():
            # Create test documents with cyclic relationships
            doc_a = OrganizationDocument.objects.create(
                dataset_version=self.version,
                identity="test:cycle:a",
                properties={
                    "name": "Org A",
                    "parents": [{"srn": "test:cycle:c", "name": "Org C"}]
                }
            )
            doc_b = OrganizationDocument.objects.create(
                dataset_version=self.version,
                identity="test:cycle:b",
                properties={
                    "name": "Org B",
                    "parents": [{"srn": "test:cycle:a", "name": "Org A"}]
                }
            )
            doc_c = OrganizationDocument.objects.create(
                dataset_version=self.version,
                identity="test:cycle:c",
                properties={
                    "name": "Org C",
                    "parents": [{"srn": "test:cycle:b", "name": "Org B"}]
                }
            )

            # Add documents to the set
            self.organization_set.documents.add(doc_a, doc_b, doc_c)

            # Run the task
            lookup_organization_parents("organizations", self.organization_set.id)

        # Refresh documents
        doc_a.refresh_from_db()
        doc_b.refresh_from_db()
        doc_c.refresh_from_db()

        # Verify that the ancestry doesn"t contain cycles
        # Each document should have at most 2 parents in its ancestry
        # (the other two in the cycle)
        self.assertLessEqual(
            len(doc_a.derivatives["lookup_organization_parents"]["parents"]), 2
        )
        self.assertLessEqual(
            len(doc_b.derivatives["lookup_organization_parents"]["parents"]), 2
        )
        self.assertLessEqual(
            len(doc_c.derivatives["lookup_organization_parents"]["parents"]), 2
        )

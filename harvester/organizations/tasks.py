from django.db.transaction import atomic
from celery import current_app as app

from harvester.tasks.base import DatabaseConnectionResetTask
from core.loading import load_harvest_models
from datagrowth.utils.iterators import ibatch


@app.task(name="lookup_organization_parents", base=DatabaseConnectionResetTask)
@atomic()
def lookup_organization_parents(app_label: str, set_ids: list[int]) -> None:
    storages = load_harvest_models(app_label)
    Set = storages.Set
    Document = storages.Document

    for organization_set in Set.objects.filter(id__in=set_ids).select_for_update():

        # Get all documents in a single query, this should be doable for memory
        documents = list(Document.objects.filter(id__in=organization_set.documents.all()).select_for_update())

        # Build a map of SRN -> document for quick lookups
        srn_to_doc = {doc.identity: doc for doc in documents}

        # First pass: collect all parent relationships and set is_root
        parent_relationships = {}
        for doc in documents:
            parents = doc.properties.get("parents", [])
            if not parents:
                # Document has no parents, it's a root
                parent_relationships[doc.identity] = {
                    "srn": doc.identity,
                    "name": doc.properties.get("name"),
                    "ror": doc.properties.get("ror"),
                    "is_root": True,
                    "parents": []
                }
            else:
                # Document has parents, collect them
                parent_relationships[doc.identity] = {
                    "srn": doc.identity,
                    "name": doc.properties.get("name"),
                    "ror": doc.properties.get("ror"),
                    "is_root": False,
                    "parents": [
                        {
                            "srn": parent.get("srn"),
                            "name": parent.get("name"),
                            "ror": parent.get("ror"),
                            "is_root": None  # Will be set in second pass
                        }
                        for parent in parents
                        if parent.get("srn") in srn_to_doc  # Only include parents that exist in our set
                    ]
                }

        # Second pass: build complete ancestry for each document and prepare for bulk update
        for doc in documents:
            ancestry = []
            current = doc.identity
            visited = set()  # Prevent cycles

            # Traverse up the parent chain
            while current in parent_relationships and current not in visited:
                visited.add(current)
                current_data = parent_relationships[current]

                # Add current to ancestry if it's not the original document
                if current != doc.identity:
                    ancestry.append({
                        "srn": current_data["srn"],
                        "name": current_data["name"],
                        "ror": current_data["ror"],
                        "is_root": current_data["is_root"]
                    })

                # Move to next parent if any
                if current_data["parents"]:
                    current = current_data["parents"][0]["srn"]
                else:
                    break

            # Update document in memory
            doc.derivatives["lookup_organization_parents"] = {
                "parents": ancestry
            }
            doc.task_results["lookup_organization_parents"] = {"success": True}

        # Bulk update documents in batches
        for batch in ibatch(documents, batch_size=100):
            Document.objects.bulk_update(batch, ["derivatives", "task_results"])

        # Update set task status
        organization_set.task_results["lookup_organization_parents"] = {"success": True}
        organization_set.save()

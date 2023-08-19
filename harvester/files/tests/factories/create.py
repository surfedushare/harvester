from django.utils.timezone import now

from files.tests.factories.datatypes import DatasetVersionFactory, SetFactory, FileDocumentFactory
from files.tests.factories.tika import HttpTikaResourceFactory


def create_file_document_set(set_specification, docs, tikas=None):
    pending_at = now()
    dataset_version = DatasetVersionFactory.create(pending_at=pending_at)
    dataset_set = SetFactory.create(dataset_version=dataset_version, name=set_specification, pending_at=pending_at)
    documents = []
    for doc in docs:
        document = FileDocumentFactory.build(
            **doc,
            dataset_version=dataset_version, collection=dataset_set, pending_at=pending_at
        )
        document.clean()
        document.save()
        documents.append(document)
    tikas = tikas or []
    for tika in tikas:
        HttpTikaResourceFactory.create(**tika)
    return dataset_version, dataset_set, documents
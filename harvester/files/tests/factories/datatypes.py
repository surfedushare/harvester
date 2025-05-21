from copy import copy
from datetime import datetime
import factory
from hashlib import sha1

from files.constants import SEED_DEFAULTS
from files.models import Dataset, DatasetVersion, Set, FileDocument


def build_file_seed(**kwargs):
    seed = copy(SEED_DEFAULTS)
    seed.update(**kwargs)
    return seed


class DatasetFactory(factory.django.DjangoModelFactory):

    name = "test"
    is_harvested = True

    class Meta:
        model = Dataset


class DatasetVersionFactory(factory.django.DjangoModelFactory):

    version = "0.0.1"
    is_current = True
    dataset = factory.SubFactory(DatasetFactory)
    created_at = datetime.now()

    class Meta:
        model = DatasetVersion


class SetFactory(factory.django.DjangoModelFactory):

    name = "test"
    dataset_version = factory.SubFactory(DatasetVersionFactory)

    class Meta:
        model = Set


class FileDocumentFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = FileDocument

    class Params:
        set = "sharekit:edusources"
        url = "https://maken.wikiwijs.nl/124977/Zorgwekkend_gedrag___kopie_1"
        mime_type = None
        title = "Zorgwekkend gedrag"
        access_rights = "OpenAccess"
        copyright = "cc-by-40"

    dataset_version = factory.SubFactory(DatasetVersionFactory)
    collection = factory.SubFactory(SetFactory)
    identity = factory.LazyAttribute(
        lambda obj: f"{obj.set}:{sha1(obj.url.encode('utf-8')).hexdigest()}"
    )

    @factory.lazy_attribute
    def properties(self):
        params = {
            attr: getattr(self, attr, SEED_DEFAULTS[attr])
            for attr in SEED_DEFAULTS
        }
        params["srn"] = self.identity
        params["set"] = self.set
        params["hash"] = sha1(self.url.encode('utf-8')).hexdigest()
        return build_file_seed(**params)

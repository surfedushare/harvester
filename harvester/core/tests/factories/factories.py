from datetime import datetime

import factory
from core.constants import DeletePolicies, HarvestStages, Repositories
from core.models import (Collection, Dataset, DatasetVersion, Document,
                         ElasticIndex, Harvest, HarvestSource,
                         HttpTikaResource)
from django.conf import settings


class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dataset

    name = "test"
    is_active = True


class DatasetVersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DatasetVersion

    version = "0.0.1"
    is_current = True
    dataset = factory.SubFactory(DatasetFactory)
    created_at = datetime.now()


class ElasticIndexFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ElasticIndex


class CollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collection


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    class Params:
        title = "Zorgwekkend gedrag"
        from_youtube = False
        analysis_allowed = True
        mime_type = "text/html"
        preview_path = None
        url = "https://maken.wikiwijs.nl/124977/Zorgwekkend_gedrag___kopie_1"
        language = "nl"

    dataset_version = factory.SubFactory(DatasetVersionFactory)
    reference = factory.Sequence(lambda n: "surfsharekit:oai:sufsharekit.nl:{}".format(n))
    properties = factory.LazyAttribute(
        lambda o: {
            "state": "active",
            "external_id": o.reference,
            "title": o.title,
            "from_youtube": o.from_youtube,
            "analysis_allowed": o.analysis_allowed,
            "mime_type": o.mime_type,
            "technical_type": settings.MIME_TYPE_TO_TECHNICAL_TYPE.get(o.mime_type, "unknown"),
            "material_types": [],
            "files": [
                [
                    o.mime_type,
                    o.url,
                    "URL 1"
                ]
            ],
            "preview_path": o.preview_path,
            "url": o.url,
            "language": {"metadata": o.language},
            "studies": [],
            "lom_educational_levels": ["WO"],
            "lowest_educational_level": 3,
            "authors": [],
            "publishers": [],
            "description": "Gedrag is zorgwekkend",
            "publisher_date": None,
            "copyright": "cc-by-40",
            "copyright_description": "http://creativecommons.org/licenses/by/4.0/",
            "aggregation_level": "2",
            "text": "blabla",
            "ideas": [],
            "has_parts": [],
            "is_part_of": [],
            "doi": None,
            "keywords": [],
            "research_object_type": None,
            "research_themes": [],
            "parties": [],
            "consortium": None,
            "learning_material_disciplines": []
        })


class HarvestSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HarvestSource

    name = "SURF Sharekit"
    repository = Repositories.EDUREP
    spec = "surf"
    delete_policy = DeletePolicies.TRANSIENT


class HarvestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Harvest

    dataset = factory.SubFactory(DatasetFactory)
    source = factory.SubFactory(HarvestSourceFactory)
    stage = HarvestStages.NEW


class HttpTikaResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = HttpTikaResource

    uri = "analyzer:9090/analyze"
    data_hash = "cca4afcf421c44223806bf089aee485f44b416c6"

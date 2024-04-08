from typing import Type

from django.conf import settings

from datagrowth.resources import HttpResource

from sources.utils.base import BaseExtractor


class PureExtractor(BaseExtractor):

    pure_api_prefix = None
    source_slug = None
    source_name = None

    @classmethod
    def _parse_file_url(cls, url):
        file_path_segment = cls.pure_api_prefix
        if file_path_segment is None or file_path_segment not in url:
            return url  # not dealing with a url we recognize as a file url
        start = url.index(file_path_segment)
        file_path = url[start + len(file_path_segment):]
        return f"{settings.SOURCES_MIDDLEWARE_API}files/{cls.source_slug}/{file_path}"

    @classmethod
    def get_provider(cls, node):
        return {
            "ror": None,
            "external_id": None,
            "slug": cls.source_slug,
            "name": cls.source_name
        }

    @classmethod
    def get_organizations(cls, node):
        root = cls.get_provider(node)
        root["type"] = "institute"
        return {
            "root": root,
            "departments": [],
            "associates": []
        }

    @classmethod
    def get_publishers(cls, node):
        return [cls.source_name]


def build_seeding_phases(resource: Type[HttpResource], objective: dict) -> list[dict]:
    resource_label = f"{resource._meta.app_label}.{resource._meta.model_name}"
    return [
        {
            "phase": "research_outputs",
            "strategy": "initial",
            "batch_size": 100,
            "retrieve_data": {
                "resource": resource_label,
                "method": "get",
                "args": [],
                "kwargs": {},
            },
            "contribute_data": {
                "objective": objective
            }
        }
    ]

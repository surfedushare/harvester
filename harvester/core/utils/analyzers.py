from enum import Enum

from django.conf import settings


class AnalyzerLanguages(Enum):
    ENGLISH = "en"
    DUTCH = "nl"
    UNKNOWN = "unk"


def get_analyzer_language(language: str) -> str:
    return language if language in settings.OPENSEARCH_LANGUAGE_CODES else AnalyzerLanguages.UNKNOWN.value

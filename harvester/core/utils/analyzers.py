from enum import Enum

from django.conf import settings


class AnalyzerLanguages(Enum):
    ENGLISH = "en"
    DUTCH = "nl"
    UNKNOWN = "unk"


def get_analyzer_language(language: str, as_enum: bool = False) -> str | AnalyzerLanguages:
    language_code = language if language in settings.OPENSEARCH_LANGUAGE_CODES else AnalyzerLanguages.UNKNOWN.value
    return AnalyzerLanguages(language_code) if as_enum else language_code

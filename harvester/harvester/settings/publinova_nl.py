from harvester.settings.base import *
from search_client import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.RESEARCH_PRODUCT

ALLOW_CLOSED_ACCESS_DOCUMENTS = True
LOWEST_EDUCATIONAL_LEVEL = -1  # will ignore lowest educational level requirements

SHAREKIT_TEST_ORGANIZATION = "Publinova test"

SIMPLE_METADATA_FREQUENCY_FIELDS = []

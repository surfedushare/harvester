from harvester.settings.base import *
from search_client import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.RESEARCH_PRODUCT

SHAREKIT_TEST_ORGANIZATIONS = [
    "Publinova test",
    "ArtEZ University of the Arts",
    "NHL Stenden Hogeschool"
]

SIMPLE_METADATA_FREQUENCY_FIELDS = []

CHECK_URL_AUTO_SUCCEED_SETS = ["saxion:kenniscentra"]
DEFAULT_FILE_TITLES_TEMPLATE = "Attachment {ix}"

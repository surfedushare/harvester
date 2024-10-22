from harvester.settings.base import *
from search_client.constants import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.RESEARCH_PRODUCT

SHAREKIT_TEST_ORGANIZATIONS = [
    "Publinova test",
    "ArtEZ University of the Arts",
    "NHL Stenden Hogeschool",
    "Hogeschool Inholland",
    "Hogeschool KPZ",
    "Christelijke Hogeschool Ede",
]

SIMPLE_METADATA_FREQUENCY_FIELDS = []

CHECK_URL_AUTO_SUCCEED_SETS = ["saxion:kenniscentra"]
DEFAULT_FILE_TITLES_TEMPLATE = "Attachment {ix}"

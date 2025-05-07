from harvester.settings.base import *
from search_client.constants import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.RESEARCH_PRODUCT

SHAREKIT_TEST_ORGANIZATIONS = [
    "Publinova test",
    "ArtEZ University of the Arts",
    "Hogeschool Inholland",
    "Hogeschool KPZ",
    "Christelijke Hogeschool Ede",
    "Hogeschool Leiden",
    "Avans Hogeschool",
    "Aeres Hogeschool",
    "Amsterdamse Hogeschool voor de Kunsten",
]

SIMPLE_METADATA_FREQUENCY_FIELDS = []

CHECK_URL_AUTO_SUCCEED_SETS = ["saxion:kenniscentra"]
DEFAULT_FILE_TITLES_TEMPLATE = "Attachment {ix}"

OPENSEARCH_PRESET_DEFAULT = "products:default"

from harvester.settings.base import *
from search_client.constants import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.RESEARCH_PRODUCT

SHAREKIT_TEST_ORGANIZATIONS = [
    "Publinova test",
    "ArtEZ University of the Arts",
    "Hogeschool KPZ",
    "Christelijke Hogeschool Ede",
    "Hogeschool Leiden",
    "Avans Hogeschool",
    "Aeres Hogeschool",
    "Amsterdamse Hogeschool voor de Kunsten",
    "Marnix Academie",
    "Driestar Educatief",
    "Hogeschool Viaa",
    "Hogeschool Rotterdam",
    "Hogeschool Windesheim",
    "HZ University of Applied Sciences",
    "HAN University of Applied Sciences",
]

SIMPLE_METADATA_FREQUENCY_FIELDS = []

CHECK_URL_AUTO_SUCCEED_SETS = ["saxion:kenniscentra", "hanze:hanze"]
DEFAULT_FILE_TITLES_TEMPLATE = "Attachment {ix}"

OPENSEARCH_PRESET_DEFAULT = "products:default"

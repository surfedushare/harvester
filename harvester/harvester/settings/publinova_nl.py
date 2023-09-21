from harvester.settings.base import *
from search_client import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.RESEARCH_PRODUCT

SHAREKIT_TEST_ORGANIZATION = "Publinova test"

SIMPLE_METADATA_FREQUENCY_FIELDS = []

# This is a temporary hard coded override that's hard to achieve with environment variables alone.
# Can be removed if Edusources and Publinova agree on what source to use for Sharekit on acceptance.
if MODE == "acceptance":
    SHAREKIT_BASE_URL = "https://api.acc.surfsharekit.nl"

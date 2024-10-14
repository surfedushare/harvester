from harvester.settings.base import *
from search_client.constants import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.LEARNING_MATERIAL

SHAREKIT_TEST_ORGANIZATIONS = ["SURF edusources test"]

SIMPLE_METADATA_FREQUENCY_FIELDS = ["study_vocabulary"]

SET_PRODUCT_COPYRIGHT_BY_MAIN_FILE_COPYRIGHT = True

# This is a temporary override to allow testing new Sharekit features using Edusources acceptance.
if MODE == "acceptance":
    SHAREKIT_BASE_URL = "https://api.acc.surfsharekit.nl"

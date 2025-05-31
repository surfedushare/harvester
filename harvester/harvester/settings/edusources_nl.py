from harvester.settings.base import *
from search_client.constants import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.LEARNING_MATERIAL

SHAREKIT_TEST_ORGANIZATIONS = ["SURF edusources test"]

SIMPLE_METADATA_FREQUENCY_FIELDS = ["study_vocabulary"]

SET_PRODUCT_COPYRIGHT_BY_MAIN_FILE_COPYRIGHT = False

# Creating a soft test on remotes to see if Edusources team updated their s***
if MODE != "localhost":
    OPENSEARCH_PRESET_DEFAULT = "products:default"
    OPENSEARCH_STRICT_MULTILINGUAL_FIELDS = True

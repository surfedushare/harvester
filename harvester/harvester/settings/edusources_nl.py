from harvester.settings.base import *
from search_client.constants import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.LEARNING_MATERIAL

SHAREKIT_TEST_ORGANIZATIONS = ["SURF edusources test"]

SIMPLE_METADATA_FREQUENCY_FIELDS = ["study_vocabulary"]

SET_PRODUCT_COPYRIGHT_BY_MAIN_FILE_COPYRIGHT = False

# Disables legacy indices for non-production in the hope things get updated
# Localhost is required for testing which should change. Publinova should be the main test target going forward.
if MODE not in ["localhost", "production"]:
    OPENSEARCH_PRESET_DEFAULT = "products:default"
    OPENSEARCH_STRICT_MULTILINGUAL_FIELDS = True

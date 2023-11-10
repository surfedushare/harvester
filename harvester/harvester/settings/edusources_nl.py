from harvester.settings.base import *
from search_client import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.LEARNING_MATERIAL

SHAREKIT_TEST_ORGANIZATION = "SURF edusources test"

SIMPLE_METADATA_FREQUENCY_FIELDS = ["study_vocabulary"]

# This is a temporary hard coded override that's overkill to add to invoke configuration.
# Can be removed if MBO gets permanently added to Edusources
if MODE in ["development"]:
    EDUREP_MBO_EDUCATIONAL_LEVEL = True

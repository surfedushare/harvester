from harvester.settings.base import *
from search_client.constants import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.LEARNING_MATERIAL

SHAREKIT_TEST_ORGANIZATIONS = ["SURF edusources test"]

SIMPLE_METADATA_FREQUENCY_FIELDS = ["study_vocabulary"]

SET_PRODUCT_COPYRIGHT_BY_MAIN_FILE_COPYRIGHT = True

# This is a temporary hard coded override that's hard to achieve with environment variables alone.
# Can be removed if Edusources no longer wants to test OERWizard on Sharekit acceptance.
# Changing this setting in this file means it only propagates to Edusources and not Publinova or MBO.
if MODE == "acceptance":
    SOURCES["sharekit"]["endpoint"] = "https://api.acc.surfsharekit.nl"

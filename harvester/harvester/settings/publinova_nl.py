from harvester.settings.base import *
from search_client import DocumentTypes


DOCUMENT_TYPE = DocumentTypes.RESEARCH_PRODUCT

ALLOW_CLOSED_ACCESS_DOCUMENTS = True
LOWEST_EDUCATIONAL_LEVEL = -1  # will ignore lowest educational level requirements

SHAREKIT_TEST_ORGANIZATION = "Publinova test"

# While Zooma develops against our development environment we switch to DEBUG=False
# To do this we need to loosen IP restrictions. We want to prevent leaking debug information to the world.
if environment.service.env == "development":
    DEBUG = False

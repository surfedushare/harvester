import os
from harvester.package import PACKAGE as HARVESTER_PACKAGE


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARVESTER_DIR = os.path.join(ROOT_DIR, "harvester")

TARGETS = {
    "harvester": HARVESTER_PACKAGE
}

from core.models.datatypes.document import HarvestDocument
from core.models.datatypes.overwrite import HarvestOverwrite


class FileDocument(HarvestDocument):
    pass


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "file overwrite"
        verbose_name_plural = "file overwrites"

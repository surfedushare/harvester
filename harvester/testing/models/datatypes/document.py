from core.models.datatypes import HarvestDocument, HarvestOverwrite


class TestingDocument(HarvestDocument):
    pass


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "testing overwrite"
        verbose_name_plural = "testing overwrites"

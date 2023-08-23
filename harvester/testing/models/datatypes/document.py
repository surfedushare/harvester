from core.models.datatypes import HarvestDocument, HarvestOverwrite


class TestDocument(HarvestDocument):
    pass


class Overwrite(HarvestOverwrite):

    class Meta:
        verbose_name = "test overwrite"
        verbose_name_plural = "test overwrites"

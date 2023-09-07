from core.models.harvest import HarvestState as AbstractHarvestState


class HarvestState(AbstractHarvestState):

    class Meta:
        verbose_name = "file harvest state"
        verbose_name_plural = "file harvest states"

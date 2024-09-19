from core.models.harvest import HarvestState as AbstractHarvestState


class HarvestState(AbstractHarvestState):

    class Meta:
        verbose_name = "project harvest state"
        verbose_name_plural = "project harvest states"

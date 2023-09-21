from core.models.harvest import HarvestState as AbstractHarvestState


class HarvestState(AbstractHarvestState):

    class Meta:
        verbose_name = "testing harvest state"
        verbose_name_plural = "testing harvest states"

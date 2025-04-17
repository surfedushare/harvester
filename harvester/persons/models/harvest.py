from core.models.harvest import HarvestState as AbstractHarvestState


class HarvestState(AbstractHarvestState):

    class Meta:
        verbose_name = "person harvest state"
        verbose_name_plural = "person harvest states"

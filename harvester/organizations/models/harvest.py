from core.models.harvest import HarvestState as AbstractHarvestState


class HarvestState(AbstractHarvestState):

    class Meta:
        verbose_name = "organization harvest state"
        verbose_name_plural = "organization harvest states"

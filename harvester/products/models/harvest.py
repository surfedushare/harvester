from core.models.harvest import HarvestState as AbstractHarvestState


class HarvestState(AbstractHarvestState):

    class Meta:
        verbose_name = "product harvest state"
        verbose_name_plural = "product harvest states"

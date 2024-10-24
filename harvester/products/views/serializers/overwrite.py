
from core.views.overwrite import OverwriteSerializer, MetricsOverwriteSerializer
from products.models import Overwrite


class ProductOverwriteSerializer(OverwriteSerializer):

    metrics = MetricsOverwriteSerializer(write_only=True)

    class Meta:
        model = Overwrite
        fields = ("id", "srn", "created_at", "modified_at", "properties", "metrics",)

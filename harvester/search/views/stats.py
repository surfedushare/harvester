from rest_framework import generics
from rest_framework import serializers
from rest_framework.permissions import AllowAny

from harvester.schema import HarvesterSchema
from search.clients import get_search_client
from search.views.base import validate_presets


class StatsSerializer(serializers.Serializer):

    documents = serializers.IntegerField()
    products = serializers.IntegerField(default=None, allow_null=True)


class SearchStatsAPIView(generics.RetrieveAPIView):
    """
    This endpoint gives information about the documents in the search engine.

    You can think of a search engine as a database table,
    but instead of rows there are "documents", which are optimized for search.

    ## Response body

    **documents**: The sum of all documents present in Open Search

    **products**: The sum of all products present in Open Search

    """
    permission_classes = (AllowAny,)
    serializer_class = StatsSerializer
    schema = HarvesterSchema()

    def get_object(self):
        presets = validate_presets(self.request)
        client = get_search_client(presets=presets)
        stats = client.stats()
        if isinstance(stats, int):
            return {"documents": client.stats()}
        return stats

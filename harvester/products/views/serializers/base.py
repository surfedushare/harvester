from rest_framework import serializers


class VideoSerializer(serializers.Serializer):
    embed_url = serializers.URLField()
    duration = serializers.CharField()


class PreviewsSerializer(serializers.Serializer):
    full_size = serializers.URLField()
    preview = serializers.URLField()
    preview_small = serializers.URLField()


class FileSerializer(serializers.Serializer):
    srn = serializers.CharField()
    hash = serializers.CharField()
    access_rights = serializers.CharField()
    state = serializers.ChoiceField(
        choices=['active', 'deleted', 'archived'],
        default='active'
    )
    is_link = serializers.BooleanField(default=False)
    url = serializers.URLField(allow_null=True, default=None)
    type = serializers.CharField(allow_null=True, default=None)
    title = serializers.CharField(allow_null=True, default=None)
    copyright = serializers.CharField(allow_null=True, default=None)
    mime_type = serializers.CharField(allow_null=True, default=None)
    video = VideoSerializer(allow_null=True, default=None)
    previews = PreviewsSerializer(allow_null=True, default=None)
    priority = serializers.IntegerField(default=0)


class AuthorSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField(allow_null=True, default=None)
    external_id = serializers.CharField(
        allow_null=True,
        default=None,
        help_text="The id of the author in the source system."
    )
    dai = serializers.CharField(allow_null=True, default=None)
    isni = serializers.CharField(allow_null=True, default=None)
    orcid = serializers.CharField(allow_null=True, default=None)
    is_external = serializers.BooleanField(
        allow_null=True,
        default=None,
        help_text="This means external author for the Provider of a Product."
    )


class StarRatingsSerializer(serializers.Serializer):
    average = serializers.FloatField(default=0.0)
    star_1 = serializers.IntegerField(default=0)
    star_2 = serializers.IntegerField(default=0)
    star_3 = serializers.IntegerField(default=0)
    star_4 = serializers.IntegerField(default=0)
    star_5 = serializers.IntegerField(default=0)


class MetricsSerializer(serializers.Serializer):
    views = serializers.IntegerField(default=0)
    stars = StarRatingsSerializer()


class BaseSearchResultSerializer(serializers.Serializer):

    entity = serializers.CharField()
    srn = serializers.CharField()
    set = serializers.CharField()
    state = serializers.CharField(default="active")
    external_id = serializers.CharField()
    score = serializers.FloatField(default=0.0)
    provider = serializers.CharField(default=None, allow_null=True)
    published_at = serializers.CharField(allow_null=True)
    modified_at = serializers.DateField(allow_null=True)
    url = serializers.URLField(allow_null=True)
    title = serializers.CharField(allow_null=True, allow_blank=True)
    description = serializers.CharField(allow_null=True, allow_blank=True)
    language = serializers.CharField(allow_null=True)
    copyright = serializers.CharField(allow_null=True)
    video = VideoSerializer(allow_null=True, default=None)
    harvest_source = serializers.CharField()
    previews = PreviewsSerializer(allow_null=True, default=None)
    files = FileSerializer(many=True)
    authors = AuthorSerializer(many=True)
    has_parts = serializers.ListField(child=serializers.CharField())
    is_part_of = serializers.ListField(child=serializers.CharField())
    keywords = serializers.ListField(child=serializers.CharField())
    metrics = MetricsSerializer(allow_null=True)

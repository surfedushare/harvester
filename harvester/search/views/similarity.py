from operator import xor

from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from search_client.constants import Platforms
from search.clients import get_search_client, prepare_results_for_response
from search.views.base import validate_presets, load_results_serializers
from harvester.schema import HarvesterSchema
from products.views.serializers import SimpleLearningMaterialResultSerializer, ResearchProductResultSerializer


class SimilaritySerializer(serializers.Serializer):
    external_id = serializers.CharField(write_only=True, required=False)
    srn = serializers.CharField(write_only=True, required=False)
    language = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        srn = attrs.get("srn")
        external_id = attrs.get("external_id")
        if not xor(bool(srn), bool(external_id)):
            raise ValidationError("Either a SRN or an external_id should be provided.")
        return attrs


class LearningMaterialSimilaritySerializer(SimilaritySerializer):
    results = SimpleLearningMaterialResultSerializer(many=True, read_only=True)
    results_total = serializers.DictField(read_only=True)


class ResearchProductSimilaritySerializer(SimilaritySerializer):
    results = ResearchProductResultSerializer(many=True, read_only=True)
    results_total = serializers.DictField(read_only=True)


class AuthorSuggestionSerializer(serializers.Serializer):
    author_name = serializers.CharField(write_only=True, required=True)


class LearningMaterialAuthorSuggestionSerializer(AuthorSuggestionSerializer):
    results = SimpleLearningMaterialResultSerializer(many=True, read_only=True)
    results_total = serializers.DictField(read_only=True)


class ResearchProductAuthorSuggestionSerializer(AuthorSuggestionSerializer):
    results = ResearchProductResultSerializer(many=True, read_only=True)
    results_total = serializers.DictField(read_only=True)


class SimilarityAPIView(GenericAPIView):
    """
    This endpoint returns similar documents as the input document.
    These similar documents can be offered as suggestions to look at for the user.
    """
    permission_classes = (AllowAny,)
    schema = HarvesterSchema()

    def get_serializer_class(self):
        if settings.PLATFORM in [Platforms.EDUSOURCES, Platforms.MBODATA]:
            return LearningMaterialSimilaritySerializer
        elif settings.PLATFORM is Platforms.PUBLINOVA:
            return ResearchProductSimilaritySerializer
        else:
            raise AssertionError("SimilarityAPIView expected application to use different PLATFORM")

    def get(self, request, *args, **kwargs):
        presets = validate_presets(self.request)
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        external_id = serializer.validated_data.get("external_id", None)
        identifier = serializer.validated_data.get("srn", external_id)
        language = serializer.validated_data["language"]
        client = get_search_client(presets=presets)
        response = client.more_like_this(identifier, language, is_external_identifier=bool(external_id))
        result_serializers = load_results_serializers(presets)
        response["results"] = prepare_results_for_response(response["results"], result_serializers)
        return Response(response)


class AuthorSuggestionsAPIView(GenericAPIView):
    """
    This endpoint returns documents where the name of the author appears in the text or metadata,
    but is not set as author in the authors field.
    These documents can be offered to authors as suggestions for more content from their hand.
    """
    permission_classes = (AllowAny,)
    schema = HarvesterSchema()

    def get_serializer_class(self):
        if settings.PLATFORM in [Platforms.EDUSOURCES, Platforms.MBODATA]:
            return LearningMaterialAuthorSuggestionSerializer
        elif settings.PLATFORM is Platforms.PUBLINOVA:
            return ResearchProductAuthorSuggestionSerializer
        else:
            raise AssertionError("AuthorSuggestionsAPIView expected application to use different PLATFORM")

    def get(self, request, *args, **kwargs):
        presets = validate_presets(self.request)
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        author_name = serializer.validated_data["author_name"]
        client = get_search_client(presets=presets)
        response = client.author_suggestions(author_name)
        result_serializers = load_results_serializers(presets)
        response["results"] = prepare_results_for_response(response["results"], result_serializers)
        return Response(response)

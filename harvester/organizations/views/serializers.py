from typing import Literal

from rest_framework import serializers
from pydantic import BaseModel, Field, field_serializer
from search_client.serializers.core import Provider, EntityStates


class Organization(BaseModel):

    entity: Literal["organization"] = Field(default="organization", init=False)
    srn: str
    set: str
    provider: Provider | str | None = Field(default=None)
    state: EntityStates = Field(default=EntityStates.ACTIVE)

    name: str
    description: str | None = Field(default=None)
    ror: str | None = Field(default=None)
    type: str
    secretary: bool = Field(default=False)
    parents: list[str] = Field(default=[])

    @field_serializer("provider")
    def serialize_provider(self, provider: Provider, _info) -> str:
        if isinstance(provider, str):
            return provider
        elif provider.name:
            return provider.name
        elif provider.slug:
            return provider.slug
        elif provider.ror:
            return provider.ror
        elif provider.external_id:
            return provider.external_id


class OrganizationSerializer(serializers.Serializer):

    entity = serializers.CharField()
    srn = serializers.CharField()
    set = serializers.CharField()
    provider = serializers.CharField(default=None, allow_null=True)
    state = serializers.CharField(default="active")

    name = serializers.CharField(allow_null=False, allow_blank=False)
    description = serializers.CharField(allow_null=True, allow_blank=False)
    ror = serializers.CharField(allow_null=True, allow_blank=False)
    type = serializers.CharField(allow_null=False, allow_blank=False)
    secretary = serializers.BooleanField(allow_null=False, default=False)
    parents = serializers.ListField(child=serializers.CharField(allow_null=False))

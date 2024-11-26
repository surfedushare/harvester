from typing import Literal

from rest_framework import serializers
from pydantic import BaseModel, Field, field_serializer
from search_client.serializers.core import Provider, EntityStates


class BaseOrganization(BaseModel):
    srn: str
    name: str
    ror: str | None = Field(default=None, description="Research Organization Registry identifier")
    is_root: bool | None = Field(default=None)


class GenericOrganization(BaseModel):
    name: str
    srn: str | None = Field(default=None)  # outside of education context a global identifier will often be missing


class Organization(BaseOrganization):

    entity: Literal["organization"] = Field(default="organization", init=False)
    set: str
    provider: Provider | str | None = Field(default=None)
    state: EntityStates = Field(default=EntityStates.ACTIVE)

    description: str | None = Field(default=None)

    type: str
    secretary: BaseOrganization | None = Field(default=None, description="Secretary of collaboration organization")
    parents: list[BaseOrganization] = Field(default=[], description="Parent organizations within educational context")
    members: list[GenericOrganization] = Field(
        default=[],
        description="Members of collaboration organizations possibly from outside the educational context"
    )

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
    secretary = serializers.DictField(allow_null=True, default=None)
    parents = serializers.ListField(child=serializers.DictField())
    members = serializers.ListField(child=serializers.DictField())

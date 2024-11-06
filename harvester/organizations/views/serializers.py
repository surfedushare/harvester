from typing import Literal

from rest_framework import serializers
from pydantic import BaseModel, Field
from search_client.serializers.core import Provider, EntityStates


class Organization(BaseModel):

    entity: Literal["organization"] = Field(default="organization", init=False)
    srn: str
    set: str
    provider: Provider | str | None = Field(default=None)
    state: EntityStates = Field(default=EntityStates.ACTIVE)

    name: str
    ror: str | None = Field(default=None)


class OrganizationSerializer(serializers.Serializer):

    entity = serializers.CharField()
    srn = serializers.CharField()
    set = serializers.CharField()
    provider = serializers.CharField(default=None, allow_null=True)
    state = serializers.CharField(default="active")

    name = serializers.CharField(allow_null=False, allow_blank=False)
    ror = serializers.CharField(allow_null=True, allow_blank=False)

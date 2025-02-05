from pydantic import BaseModel, Field, HttpUrl

from search_client.serializers.core import EntityStates


class PydanticDocument(BaseModel):
    srn: str
    set: str
    external_id: str
    state: EntityStates = Field(default=EntityStates.ACTIVE)
    url: HttpUrl
    title: str | None = Field(default=None)
    access_rights: str = Field(default="OpenAccess")
    copyright: str | None = Field(default=None)

from typing import Any
from json import JSONDecoder
from dateutil.parser import isoparse


class HarvesterJSONDecoder(JSONDecoder):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(object_pairs_hook=self.decode_object_items, *args, **kwargs)

    def decode_object_items(self, items: Any) -> dict:
        obj = {}
        for key, value in items:
            if key.endswith("_at") and value:
                value = isoparse(value)
            obj[key] = value
        return obj

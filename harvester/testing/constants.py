SEED_DEFAULTS = {
    "state": "active",
    "srn": None,
    "external_id": None,
    "url": None,
    "title": None
}

ENTITY_SEQUENCE_PROPERTIES = {
    "simple": {
        "srn": "surf:testing:{ix}",
        "external_id": "{ix}",  # will be cast to an int
        "url": "http://localhost:8888/file/{ix}",
        "title": "title for {ix}"
    },
    "nested": {
        "srn": "surf:testing:{ix}"
    }
}

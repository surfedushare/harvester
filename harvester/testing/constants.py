SEED_DEFAULTS = {
    # Essential keys for functioning of the system
    "state": "active",
    "external_id": None,
    "set": "surf:testing",
    # Generic metadata
    "url": None,
    "title": None,
    "access_rights": "OpenAccess",
    "copyright": None
}

ENTITY_SEQUENCE_PROPERTIES = {
    "simple": {
        "external_id": "{ix}",  # will be cast to an int
        "url": "http://testserver/file/{ix}",
        "title": "title for {ix}"
    },
    "nested": {
        "external_id": "{ix}",  # will be cast to an int
        "url": "http://testserver/file/{ix}",
        "title": "title for {ix}"
    },
    "merge": {
        "external_id": "{ix}",  # will be cast to an int
        "url": "http://testserver/file/{ix}",
        "title": "title for {ix}"
    }
}

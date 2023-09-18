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
        "url": "http://localhost:8888/file/{ix}",
        "title": "title for {ix}"
    },
    "nested": {
        "external_id": "{ix}",  # will be cast to an int
        "url": "http://localhost:8888/file/{ix}",
        "title": "title for {ix}"
    },
    "merge": {
        "state": "deleted",  # to create pre-existing documents for delete_policy=no sources
        "external_id": "{ix}",  # will be cast to an int
        "url": "http://localhost:8888/file/{ix}",
        "title": "title for {ix}"
    }
}

SEED_DEFAULTS = {
    # Essential keys for functioning of the system
    "state": None,
    "set": None,
    "external_id": None,
    # Generic metadata
    "modified_at": None,
    "files": [],
    "technical_type": None,
    "title": None,
    "subtitle": None,
    "language": None,
    "keywords": [],
    "description": None,
    "copyright": None,
    "copyright_description": None,
    "authors": [],
    "provider": {},
    "organizations": [],
    "publishers": [],
    "publisher_date": None,
    "publisher_year": None,
    "is_part_of": [],
    "has_parts": [],
    "doi": None,
    # Learning material metadata
    "learning_material": {
        "material_types": ["unknown"],
        "aggregation_level": None,
        "lom_educational_levels": [],
        "studies": [],
        "study_vocabulary": [],
        "disciplines": [],
        "consortium": None,
        # MBO specific fields.
        # The field doesn't agree across which dimension to categorize materials.
        # So for now we use two types of category that are very similar in scope.
        "industries": [],
        "sectors": []
    },
    # Research product metadata
    "research_product": {
        "research_object_type": None,
        "research_themes": [],
        "parties": [],
        "projects": []
    }
}

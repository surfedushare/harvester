from metadata.models import MetadataField, MetadataValue, MetadataTranslation
from metadata.utils.translate import translate_with_deepl


def normalize_field_values(field_name: str, *args, is_singular: bool = False, as_models=False):
    if not args:
        return None if is_singular else []
    assert len(args) == 1 or not is_singular, "Expected only one value when normalizing to a single value"

    value_filters = {
        "field__name": field_name
    }
    if is_singular:
        value_filters["value"] = args[0]
    else:
        value_filters["value__in"] = args
    metadata_values = MetadataValue.objects.select_related("translation").filter(**value_filters)

    normalized_values = set()
    for metadata_value in metadata_values:
        try:
            root = metadata_value.get_root()
        except MetadataValue.DoesNotExist:
            normalized_values.add(metadata_value if as_models else metadata_value.value)
            continue
        node = root if root is not None else metadata_value
        normalized_values.add(node if as_models else node.value)
    normalized_values = list(normalized_values)

    if not normalized_values:
        return None if is_singular else normalized_values
    return normalized_values[0] if is_singular else normalized_values


def get_or_create_metadata_value(term: str, field: MetadataField, parent: MetadataValue | None = None,
                                 nl: str | None = None, en: str | None = None) -> MetadataValue:
    try:
        return MetadataValue.objects.get(value=term, field=field)
    except MetadataValue.DoesNotExist:
        pass
    en = en or translate_with_deepl(nl)
    translation = MetadataTranslation.objects.create(nl=nl, en=en, is_fuzzy=True)
    return MetadataValue.objects.create(
        name=nl,
        field=field,
        parent=parent,
        value=term,
        translation=translation,
        is_manual=True
    )


def get_or_create_metadata_field(field: str, entity: str, nl: str, en: str,
                                 english_as_dutch: bool = False) -> MetadataField:
    try:
        return MetadataField.objects.get(name=field, entity=entity)
    except MetadataField.DoesNotExist:
        pass
    translation = MetadataTranslation.objects.create(nl=nl, en=en, is_fuzzy=True)
    return MetadataField.objects.create(
        name=field,
        entity=entity,
        translation=translation,
        is_hidden=True,
        is_manual=False,  # setting this to true is considered deprecated
        english_as_dutch=english_as_dutch
    )

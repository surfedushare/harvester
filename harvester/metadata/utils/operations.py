from metadata.models import MetadataValue


def normalize_field_values(field_name: str, *args, is_singular: bool = False):
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
    metadata_values = MetadataValue.objects.filter(**value_filters)

    normalized_values = set()
    for metadata_value in metadata_values:
        try:
            root = metadata_value.get_root()
        except MetadataValue.DoesNotExist:
            normalized_values.add(metadata_value.value)
            continue
        normalized_values.add(root.value if root is not None else metadata_value.value)
    normalized_values = list(normalized_values)

    if not normalized_values:
        return None if is_singular else normalized_values
    return normalized_values[0] if is_singular else normalized_values

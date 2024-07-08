from rest_framework.schemas.openapi import AutoSchema


class HarvesterSchema(AutoSchema):

    def _get_operation_id(self, path, method):
        operation_id = path.replace("/", "-").strip("-")
        return f"{method.lower()}-{operation_id}"

    def _map_field(self, field):
        if field.field_name == "children":
            return {
                'type': 'array',
                'items': {
                    "properties": "as parent"
                }
            }
        return super()._map_field(field)

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if path.startswith("/product"):
            operation["tags"] = [f"Download products"]
            for parameter in operation["parameters"]:
                if parameter["name"] == "page":
                    parameter["schema"]["default"] = 1
                if parameter["name"] == "page_size":
                    parameter["schema"]["default"] = 10
            if not path.endswith("/{srn}/"):
                operation["parameters"] += [
                    {
                        "name": "modified_since",
                        "in": "query",
                        "required": False,
                        "description": "Specify from which point in time onward "
                                       "you want to get changes to the product entities.",
                        'schema': {
                            'type': 'datetime',
                        }
                    }
                ]
        elif path.startswith("/extension"):
            operation["tags"] = ["Extending data"]
        elif path.startswith("/search") or path.startswith("/find"):
            operation["tags"] = ["Search"]
            if "search/documents" in path:
                operation["parameters"] += [
                    {
                        "name": "include_filter_counts",
                        "in": "query",
                        "required": False,
                        "description": "When set to 1 the response will include the counts of documents "
                                       "per combination of metadata field and metadata value "
                                       "in the filter_counts property",
                        'schema': {
                            'type': 'number',
                        }
                    }
                ]
            if "search/autocomplete" in path:
                operation["parameters"] += [
                    {
                        "name": "query",
                        "in": "query",
                        "required": True,
                        "description": "The search query you want to autocomplete for.",
                        'schema': {
                            'type': 'string',
                        }
                    }
                ]
        elif path.startswith("/suggestions"):
            operation["tags"] = ["Suggestions"]
            if "similarity" in path:
                operation["parameters"] += [
                    {
                        "name": "srn",
                        "in": "query",
                        "required": False,
                        "description": "The SRN of the document you want similar documents for.",
                        'schema': {
                            'type': 'string',
                        }
                    },
                    {
                        "name": "external_id",
                        "in": "query",
                        "required": False,
                        "description": "The external_id of the document you want similar documents for "
                                       "(using SRN instead of external_id is recommended).",
                        'schema': {
                            'type': 'string',
                        }
                    },
                    {
                        "name": "language",
                        "in": "query",
                        "required": True,
                        "description": "The language of the document you want similar documents for.",
                        'schema': {
                            'type': 'string',
                        }
                    }
                ]
            if "author" in path:
                operation["parameters"] += [
                    {
                        "name": "author_name",
                        "in": "query",
                        "required": True,
                        "description": "The name of the author you want documents for.",
                        'schema': {
                            'type': 'string',
                        }
                    }
                ]
        elif path.startswith("/metadata"):
            operation["tags"] = ["Metadata"]
            if "tree" in path:
                operation["parameters"] += [
                    {
                        "name": "max_children",
                        "in": "query",
                        "required": False,
                        "description": "Limits the amount of children returned by this endpoint "
                                       "(mostly useful to speed up responses from the interactive documentation)",
                        'schema': {
                            'type': 'string',
                        }
                    },
                ]
        else:
            operation["tags"] = ["default"]
        return operation

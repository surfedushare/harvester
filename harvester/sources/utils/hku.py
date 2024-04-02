from sources.utils.base import BaseExtractor


class HkuExtractor(BaseExtractor):

    @classmethod
    def build_product_id(cls, identifier):
        if not identifier:
            return identifier
        return f"hku:product:{identifier}"

    @classmethod
    def build_person_id(cls, identifier):
        if not identifier:
            return identifier
        return f"hku:person:{identifier}"

    @classmethod
    def build_full_name(cls, person):
        match person:
            case {"first_name": first_name, "last_name": last_name, "prefix": prefix} if person.get("prefix"):
                full_name = f"{first_name} {prefix} {last_name}"
            case {"first_name": first_name, "last_name": last_name} if person.get("first_name"):
                full_name = f"{first_name} {last_name}"
            case {"last_name": last_name}:
                full_name = last_name
            case _:
                full_name = None
        return full_name

    @classmethod
    def get_external_id(cls, node):
        identifier = node["resultid"] or None
        return cls.build_product_id(identifier)

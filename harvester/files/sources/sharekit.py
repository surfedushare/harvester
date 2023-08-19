from hashlib import sha1


def get_file_seeds(sharekit_products_data: dict):
    """
    This function takes a Sharekit publication API response and transforms it into file dicts.
    File dicts have at least an "url" key that indicates where we can find the file.
    The "srn" key contains a unique identifier for the "url".
    The "is_link" key indicates whether we should treat the "url" as an actual link instead of a file link.

    :param sharekit_products_data: a parsed Sharekit publication API response
    :return: yields file objects
    """
    for sharekit_product in sharekit_products_data["data"]:
        product_id = sharekit_product["id"]
        product_attributes = sharekit_product["attributes"]
        product_copyright = product_attributes.get("termsOfUse", None)
        product_files = product_attributes.get("files", []) or []
        product_links = product_attributes.get("links", []) or []
        for product_file in product_files:
            # Anything without a URL can not be processed
            if not product_file.get("url", None):
                continue
            # We add some product metadata, because unfortunately the product supplies defaults
            product_file["product"] = {
                "provider": "sharekit",
                "product_id": product_id,
                "copyright": product_copyright,
                "type": "file"
            }
            # We indicate we're not dealing with a webpage URL
            product_file["is_link"] = False
            yield product_file
        for product_link in product_links:
            # Anything without a URL can not be processed
            if not product_link.get("url", None):
                continue
            product_link["product"] = {
                "provider": "sharekit",
                "product_id": product_id,
                "copyright": product_copyright,
                "type": "link"
            }
            # We indicate that the URL points to a webpage
            product_link["is_link"] = True
            yield product_link


class SharekitFileExtraction(object):

    @classmethod
    def get_hash(cls, node: dict) -> str:
        return sha1(node["url"].encode("utf-8")).hexdigest()

    @classmethod
    def get_srn(cls, node: dict) -> str:
        identifier = cls.get_hash(node)
        return f"sharekit:{node['product']['provider']}:{identifier}"

    @classmethod
    def get_mime_type(cls, node: dict) -> str:
        mime_type = node.get("resourceMimeType", None)
        if mime_type is None and node["is_link"]:
            mime_type = "text/html"
        return mime_type

    @classmethod
    def get_access_rights(cls, node: dict) -> str:
        access_rights = node["accessRight"]
        if access_rights[0].isupper():  # value according to standard; no parsing necessary
            return access_rights
        access_rights = access_rights.replace("access", "")
        access_rights = access_rights.capitalize()
        access_rights += "Access"
        return access_rights


OBJECTIVE = {
    "@": get_file_seeds,
    "srn": SharekitFileExtraction.get_srn,
    "url": lambda node: node["url"],
    "hash": SharekitFileExtraction.get_hash,
    "mime_type": SharekitFileExtraction.get_mime_type,
    "title": lambda node: node.get("fileName", node.get("urlName", None)),
    "copyright": lambda node: node["product"]["copyright"],
    "access_rights": SharekitFileExtraction.get_access_rights,
    "product_id": lambda node: node["product"]["product_id"],
    "is_link": lambda node: node["is_link"],
    "harvest_source": lambda node: "sharekit",
    "provider": lambda node: node["product"]["provider"]
}


SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 5,
        "retrieve_data": {
            "resource": "sharekit.sharekitmetadataharvest",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]
import os
import re
from hashlib import sha1
from dateutil.parser import ParserError, parse as date_parser

import vobject
from django.conf import settings
from django.utils.text import slugify


class GreeniDataExtraction(object):

    youtube_regex = re.compile(r".*(youtube\.com|youtu\.be).*", re.IGNORECASE)
    cc_url_regex = re.compile(r"^https?://creativecommons\.org/(?P<type>\w+)/(?P<license>[a-z\-]+)/(?P<version>\d\.\d)",
                              re.IGNORECASE)
    cc_code_regex = re.compile(r"^cc([ \-][a-z]{2})+$", re.IGNORECASE)

    #############################
    # OAI-PMH
    #############################

    @classmethod
    def parse_copyright_description(cls, description):
        if description is None:
            return
        url_match = cls.cc_url_regex.match(description)
        if url_match is None:
            code_match = cls.cc_code_regex.match(description)
            return slugify(description.lower()) if code_match else None
        license = url_match.group("license").lower()
        if license == "mark":
            license = "pdm"
        elif license == "zero":
            license = "cc0"
        else:
            license = "cc-" + license
        return slugify(f"{license}-{url_match.group('version')}")

    @staticmethod
    def parse_vcard_element(el):
        card = "\n".join(field.strip() for field in el.text.strip().split("\n"))
        return vobject.readOne(card)

    @classmethod
    def get_oaipmh_records(cls, soup):
        return soup.find_all('record')

    @classmethod
    def get_oaipmh_external_id(cls, soup, el):
        return el.find('identifier').text.strip()

    @classmethod
    def get_oaipmh_record_state(cls, soup, el):
        header = el.find('header')
        return header.get("status", "active")

    #############################
    # GENERIC
    #############################

    @classmethod
    def find_resources(cls, xml, resource_type):
        resource_code = None
        if resource_type == "file":
            resource_code = "objectFile"
        elif resource_type == "link":
            resource_code = "humanStartPage"
        elif resource_type == "meta":
            resource_code = "descriptiveMetadata"
        resource_identifier = f"info:eu-repo/semantics/{resource_code}"
        return xml.find_all("rdf:type", attrs={"rdf:resource": resource_identifier})

    @classmethod
    def find_metadata(cls, xml):
        resources = cls.find_resources(xml, "meta")
        if not resources:
            return
        elif len(resources) > 1:
            raise AssertionError(f"Unexpected length for metadata resource: {len(resources)}")
        metadata = resources[0]
        item = next((parent for parent in metadata.parents if parent.name == "didl:item"), None)
        if not item:
            raise AssertionError("Metadata descriptor did not have an item as parent")
        return item.find("didl:resource")

    @classmethod
    def _extract_file(cls, resource_type, resource, ix):
        item = next((parent for parent in resource.parents if parent.name == "didl:item"), None)
        if not item:
            return
        element = item.find("didl:resource")
        if not element:
            return
        url = element["ref"]
        match resource_type:
            case "file":
                title = f"Attachment {ix+1}"
            case "link":
                title = f"URL {ix+1}"
            case _:
                title = None
        return {
            "mime_type": element.get("mimetype", None),
            "url": url,
            "hash": sha1(url.encode("utf-8")).hexdigest(),
            "title": title
        }

    @classmethod
    def get_files(cls, soup, el):
        file_resources = cls.find_resources(el, "file")
        link_resources = cls.find_resources(el, "link")
        results = []
        for ix, resource in enumerate(file_resources):
            results.append(cls._extract_file("file", resource, ix))
        for ix, resource in enumerate(link_resources):
            results.append(cls._extract_file("link", resource, ix))
        return results

    @classmethod
    def get_url(cls, soup, el):
        files = cls.get_files(soup, el)
        if not len(files):  # happens when a record was deleted
            return
        return files[0]["url"].strip()

    @classmethod
    def get_mime_type(cls, soup, el):
        files = cls.get_files(soup, el)
        if not len(files):  # happens when a record was deleted
            return
        return files[0]["mime_type"].strip() if files[0]["mime_type"] else None

    @classmethod
    def get_copyright(cls, soup, el):
        access_rights = el.find("dcterms:accessrights")
        if not access_rights:
            return
        if access_rights.text.strip() == "http://purl.org/eprint/accessRights/OpenAccess":
            return "open-access"
        return "yes"

    @classmethod
    def get_language(cls, soup, el):
        metadata = cls.find_metadata(el)
        if not metadata:
            return
        language_term = metadata.find("languageterm")
        language_code = language_term.text.strip()
        if language_code == "dut":
            return "nl"
        elif language_code == "eng":
            return "en"
        return "unk"

    @classmethod
    def get_title(cls, soup, el):
        node = el.find('title')
        return node.text.strip() if node else None

    @classmethod
    def get_description(cls, soup, el):
        node = el.find('abstract')
        return node.text if node else None

    @classmethod
    def get_authors(cls, soup, el):
        roles = el.find_all(string='aut')
        if not roles:
            return []
        authors = []
        for role in roles:
            author = role.find_parent('name')
            if not author:
                continue
            given_name = author.find('namepart', attrs={"type": "given"})
            family_name = author.find('namepart', attrs={"type": "family"})
            if not given_name and not family_name:
                continue
            elif not given_name:
                name = family_name.text.strip()
            elif not family_name:
                name = given_name.text.strip()
            else:
                name = f"{given_name.text.strip()} {family_name.text.strip()}"
            authors.append({
                "name": name,
                "email": None,
                "external_id": None,
                "dai": None,
                "orcid": None,
                "isni": None,
            })
        return authors

    @classmethod
    def get_publishers(cls, soup, el):
        publisher = el.find("publisher")
        return [publisher.text.strip()] if publisher else []

    @classmethod
    def get_publisher_year(cls, soup, el):
        date_issued = el.find("dateissued")
        if not date_issued:
            return
        datetime = None
        try:
            datetime = date_parser(date_issued.text)
        except ParserError:
            pass
        return datetime.year if datetime else None

    @classmethod
    def get_technical_type(cls, soup, el):
        mime_type = cls.get_mime_type(soup, el)
        if mime_type:
            return settings.MIME_TYPE_TO_TECHNICAL_TYPE.get(mime_type, "unknown")
        return

    @classmethod
    def get_from_youtube(cls, soup, el):
        url = cls.get_url(soup, el)
        if not url:
            return False
        return cls.youtube_regex.match(url) is not None

    @classmethod
    def get_is_restricted(cls, soup, el):
        return False

    @classmethod
    def get_analysis_allowed(cls, soup, el):
        # We disallow analysis for non-derivative materials as we'll create derivatives in that process
        # NB: any material that is_restricted will also have analysis_allowed set to False
        copyright = GreeniDataExtraction.get_copyright(soup, el)
        return (copyright is not None and "nd" not in copyright) and copyright != "yes"

    @classmethod
    def get_research_object_type(cls, soup, el):
        genre = el.find("genre")
        return genre.text.strip() if genre else None

    @classmethod
    def get_doi(cls, soup, el):
        identifier = el.find("identifier", attrs={"type": "doi"})
        return identifier.text.strip() if identifier else None


GREENI_EXTRACTION_OBJECTIVE = {
    # Essential NPPO properties
    "url": GreeniDataExtraction.get_url,
    "files": GreeniDataExtraction.get_files,
    "copyright": GreeniDataExtraction.get_copyright,
    "title": GreeniDataExtraction.get_title,
    "language": GreeniDataExtraction.get_language,
    "keywords": lambda soup, el: [],
    "description": GreeniDataExtraction.get_description,
    "mime_type": GreeniDataExtraction.get_mime_type,
    "authors": GreeniDataExtraction.get_authors,
    "publishers": GreeniDataExtraction.get_publishers,
    "publisher_date": lambda soup, el: None,
    "publisher_year": GreeniDataExtraction.get_publisher_year,

    # Non-essential NPPO properties
    "technical_type": GreeniDataExtraction.get_technical_type,
    "from_youtube": GreeniDataExtraction.get_from_youtube,
    "is_restricted": GreeniDataExtraction.get_is_restricted,
    "analysis_allowed": GreeniDataExtraction.get_analysis_allowed,
    "research_object_type": GreeniDataExtraction.get_research_object_type,
    "research_themes": lambda soup, el: [],
    "parties": lambda soup, el: [],
    "doi": GreeniDataExtraction.get_doi,

    # Non-essential Edusources properties (for compatibility reasons)
    "material_types": lambda soup, el: None,
    "aggregation_level": lambda soup, el: None,
    "lom_educational_levels": lambda soup, el: [],
    "studies": lambda soup, el: [],
    "ideas": lambda soup, el: [],
    "is_part_of": lambda soup, el: [],
    "has_parts": lambda soup, el: [],
    "copyright_description": lambda soup, el: None,
    "learning_material_disciplines": lambda soup, el: [],
    "consortium": lambda soup, el: None,
    "lom_educational_level": lambda soup, el: None,
    "lowest_educational_level": lambda soup, el: 2,
}

import logging
import re

from vobject.base import ParseError, readOne
from dateutil.parser import parse as date_parser
from django.utils.text import slugify


logger = logging.getLogger("harvester")


LOWEST_EDUCATIONAL_LEVEL = 2  # HBO


class EdurepDataExtraction(object):

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

    @classmethod
    def parse_vcard_element(cls, el, record):
        card = "\n".join(field.strip() for field in el.text.strip().split("\n"))
        try:
            return readOne(card)
        except ParseError:
            external_id = cls.get_oaipmh_external_id(None, record)
            logger.warning(f"Can't parse vCard for material with id: {external_id}")
            return

    @classmethod
    def get_oaipmh_records(cls, soup):
        return soup.find_all('record')

    @classmethod
    def get_oaipmh_external_id(cls, soup, el):
        return el.find('identifier').text.strip()

    @classmethod
    def get_oaipmh_record_state(cls, soup, el):
        lowest_educational_level = cls.get_lowest_educational_level(soup, el)
        if lowest_educational_level < LOWEST_EDUCATIONAL_LEVEL:
            return "inactive"
        header = el.find('header')
        return header.get("status", "active")

    #############################
    # GENERIC
    #############################

    @staticmethod
    def find_all_classification_blocks(element, classification_type, output_type):
        assert output_type in ["czp:entry", "czp:id"]
        entries = element.find_all(string=classification_type)
        blocks = []
        for entry in entries:
            classification_element = entry.find_parent('czp:classification')
            if not classification_element:
                continue
            blocks += classification_element.find_all(output_type)
        return blocks

    @classmethod
    def get_files(cls, soup, el):
        return el.find_all('czp:location')


    @classmethod
    def get_title(cls, soup, el):
        node = el.find('czp:title')
        if node is None:
            return
        translation = node.find('czp:langstring')
        return translation.text.strip() if translation else None

    @classmethod
    def get_language(cls, soup, el):
        node = el.find('czp:language')
        return node.text.strip() if node else None

    @classmethod
    def get_keywords(cls, soup, el):
        nodes = el.find_all('czp:keyword')
        return [
            node.find('czp:langstring').text.strip()
            for node in nodes
        ]

    @classmethod
    def get_description(cls, soup, el):
        node = el.find('czp:description')
        if node is None:
            return
        translation = node.find('czp:langstring')
        return translation.text if translation else None

    @classmethod
    def get_material_types(cls, soup, el):
        material_types = el.find_all('czp:learningresourcetype')
        if not material_types:
            return []
        return [
            material_type.find('czp:value').find('czp:langstring').text.strip()
            for material_type in material_types
        ]

    @classmethod
    def get_copyright(cls, soup, el):
        node = el.find('czp:copyrightandotherrestrictions')
        if node is None:
            return "yes"
        copyright = node.find('czp:value').find('czp:langstring').text.strip()
        if copyright == "yes":
            copyright = cls.parse_copyright_description(cls.get_copyright_description(soup, el))
        return copyright or "yes"

    @classmethod
    def get_aggregation_level(cls, soup, el):
        node = el.find('czp:aggregationlevel', None)
        if node is None:
            return None
        return node.find('czp:value').find('czp:langstring').text.strip() if node else None

    @classmethod
    def get_authors(cls, soup, el):
        author = el.find(string='author')
        if not author:
            return []
        contribution = author.find_parent('czp:contribute')
        if not contribution:
            return []
        nodes = contribution.find_all('czp:vcard')

        authors = []
        for node in nodes:
            author = cls.parse_vcard_element(node, el)
            if hasattr(author, "fn"):
                authors.append({
                    "name": author.fn.value.strip(),
                    "email": None,
                    "external_id": None,
                    "dai": None,
                    "orcid": None,
                    "isni": None,
                })
        return authors

    @classmethod
    def get_provider(cls, soup, el):
        provider_name = None
        publishers = cls.get_publishers(soup, el)
        if len(publishers):
            provider_name = publishers[0]
        return {
            "ror": None,
            "external_id": None,
            "slug": None,
            "name": provider_name
        }

    @classmethod
    def get_organizations(cls, soup, el):
        root = cls.get_provider(soup, el)
        root["type"] = "unknown"
        return {
            "root": root,
            "departments": [],
            "associates": []
        }

    @classmethod
    def get_consortium(cls, soup, el):
        hbovpk_keywords = [keyword for keyword in cls.get_keywords(soup, el) if "hbovpk" in keyword.lower()]
        if hbovpk_keywords:
            return "HBO Verpleegkunde"

    @classmethod
    def get_publishers(cls, soup, el):
        publishers = []
        publisher_element = el.find(string='publisher')
        if not publisher_element:
            return publishers
        contribution_element = publisher_element.find_parent('czp:contribute')
        if not contribution_element:
            return publishers
        nodes = contribution_element.find_all('czp:vcard')
        for node in nodes:
            publisher = cls.parse_vcard_element(node, el)
            if hasattr(publisher, "fn"):
                publishers.append(publisher.fn.value)
        return publishers

    @staticmethod
    def find_role_datetime(role):
        if not role:
            return
        contribution = role.find_parent('czp:contribute')
        if not contribution:
            return
        datetime = contribution.find('czp:datetime')
        if not datetime:
            return
        return datetime.text.strip()

    @classmethod
    def get_publisher_date(cls, soup, el):
        publisher = el.find(string='publisher')
        publisher_datetime = cls.find_role_datetime(publisher)
        if publisher_datetime:
            return publisher_datetime
        provider = el.find(string='content provider')
        provider_datetime = cls.find_role_datetime(provider)
        return provider_datetime

    @classmethod
    def get_publisher_year(cls, soup, el):
        publisher_date = cls.get_publisher_date(soup, el)
        if publisher_date is None:
            return
        datetime = date_parser(publisher_date)
        return datetime.year

    @classmethod
    def get_lom_educational_levels(cls, soup, el):
        educational = el.find('czp:educational')
        if not educational:
            return []
        contexts = educational.find_all('czp:context')
        if not contexts:
            return []
        educational_levels = [
            edu.find('czp:value').find('czp:langstring').text.strip()
            for edu in contexts
        ]
        return list(set(educational_levels))

    @classmethod
    def get_educational_levels(cls, soup, el):
        blocks = cls.find_all_classification_blocks(el, "educational level", "czp:entry")
        return list(set([block.find('czp:langstring').text.strip() for block in blocks]))

    @classmethod
    def get_studies(cls, soup, el):
        blocks = cls.find_all_classification_blocks(el, "discipline", "czp:id")
        return list(set([block.text.strip() for block in blocks]))

    @classmethod
    def get_ideas(cls, soup, el):
        external_id = cls.get_oaipmh_external_id(soup, el)
        if not external_id.startswith("surfsharekit"):
            return []
        blocks = cls.find_all_classification_blocks(el, "idea", "czp:entry")
        compound_ideas = list(set([block.find('czp:langstring').text.strip() for block in blocks]))
        ideas = []
        for compound_idea in compound_ideas:
            ideas += compound_idea.split(" - ")
        return list(set(ideas))

    @classmethod
    def get_is_part_of(cls, soup, el):
        return []  # not supported for now

    @classmethod
    def get_has_parts(cls, soup, el):
        return []  # not supported for now

    @classmethod
    def get_copyright_description(cls, soup, el):
        node = el.find('czp:rights')
        if not node:
            return
        description = node.find('czp:description')
        return description.find('czp:langstring').text.strip() if description else None


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": EdurepDataExtraction.get_oaipmh_records,
    "state": EdurepDataExtraction.get_oaipmh_record_state,
    "external_id": EdurepDataExtraction.get_oaipmh_external_id,
    "set": EdurepDataExtraction.get_set,
    # Generic metadata
    # "doi": ,
    # toDo: Update fixture to check if these values exist in data.
    "files": EdurepDataExtraction.get_files,
    "title": EdurepDataExtraction.get_title,
    "language": EdurepDataExtraction.get_language,
    "keywords": EdurepDataExtraction.get_keywords,
    "description": EdurepDataExtraction.get_description,
    "copyright": EdurepDataExtraction.get_copyright,
    "copyright_description": EdurepDataExtraction.get_copyright_description,
    "authors": EdurepDataExtraction.get_authors,
    "provider": EdurepDataExtraction.get_provider,
    "organizations": EdurepDataExtraction.get_organizations,
    "publishers": EdurepDataExtraction.get_publishers,
    "publisher_date": EdurepDataExtraction.get_publisher_date,
    "publisher_year": EdurepDataExtraction.get_publisher_year,
    "is_part_of": EdurepDataExtraction.get_is_part_of,
    "has_parts": EdurepDataExtraction.get_has_parts,
    # Learning material metadata
    "learning_material.aggregation_level": EdurepDataExtraction.get_aggregation_level,
    "learning_material.material_types": EdurepDataExtraction.get_material_types,
    "learning_material.lom_educational_levels": EdurepDataExtraction.get_educational_levels,
    "learning_material.studies": EdurepDataExtraction.get_studies,
    "learning_material.ideas": EdurepDataExtraction.get_ideas,
    "learning_material.study_vocabulary": lambda soup, el: [],
    "learning_material.disciplines": EdurepDataExtraction.get_studies,
    "learning_material.consortium": EdurepDataExtraction.get_consortium,
    # Research product metadata
    # "research_product.research_object_type": ,
    # "research_product.research_themes": ,
    # "research_product.parties": ,
}

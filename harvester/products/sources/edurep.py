import bs4
from datetime import datetime

from dateutil.parser import parse as date_parser

from sources.utils.edurep import EdurepExtractor


class EdurepProductExtraction:

    #############################
    # OAI-PMH
    #############################

    @classmethod
    def get_oaipmh_external_id(cls, soup, el):
        return el.find('identifier').text.strip()

    @classmethod
    def get_oaipmh_record_state(cls, soup, el):
        return EdurepExtractor.get_oaipmh_record_state(el)

    @classmethod
    def get_oaipmh_modified_at(cls, soup: bs4.BeautifulSoup, el: bs4.element.Tag) -> str:
        header = el.find("header")
        return header.find("datestamp").text.strip()

    @classmethod
    def get_set(cls, soup, el):
        return f"edurep:{el.find('setSpec').text.strip()}"

    #############################
    # GENERIC
    #############################

    @classmethod
    def get_files(cls, soup, el):
        files = []
        for file in el.find_all('czp:location'):
            files.append(EdurepExtractor.parse_url(file.text))
        return files

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
        return translation.text.strip() if translation else None

    @classmethod
    def get_material_types(cls, soup, el):
        material_types = el.find_all('czp:learningresourcetype')
        if not material_types:
            return ["unknown"]
        return [
            material_type.find('czp:value').find('czp:langstring').text.strip()
            for material_type in material_types
        ]

    @classmethod
    def get_copyright(cls, soup, el):
        return EdurepExtractor.get_copyright(el)

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
        external_id = cls.get_oaipmh_external_id(soup, el)
        for node in nodes:
            author = EdurepExtractor.parse_vcard_element(node, external_id)
            if hasattr(author, "fn"):
                authors.append({
                    "name": author.fn.value.strip(),
                    "email": None,
                    "external_id": None,
                    "dai": None,
                    "orcid": None,
                    "isni": None,
                    "is_external": None
                })
        return authors

    @classmethod
    def get_provider(cls, soup, el):
        return EdurepExtractor.get_provider(el)

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
        external_id = cls.get_oaipmh_external_id(soup, el)
        return EdurepExtractor.get_publishers(el, external_id)

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
        if provider_datetime is None:
            return
        return date_parser(
            provider_datetime,
            default=datetime(year=1970, month=1, day=1)).strftime("%Y-%m-%d")

    @classmethod
    def get_publisher_year(cls, soup, el):
        publisher_date = cls.get_publisher_date(soup, el)
        if publisher_date is None:
            return
        datetime = date_parser(publisher_date)
        return datetime.year

    @classmethod
    def get_educational_levels(cls, soup, el):
        return EdurepExtractor.get_educational_levels(el)

    @classmethod
    def get_studies(cls, soup, el):
        blocks = EdurepExtractor.find_all_classification_blocks(el, "discipline", "czp:id")
        return list(set([block.text.strip() for block in blocks]))

    @classmethod
    def get_study_vocabulary(cls, soup, el):
        studies = cls.get_studies(soup, el)
        return [
            f"http://purl.edustandaard.nl/concept/{study}"
            for study in studies
        ]

    @classmethod
    def get_copyright_description(cls, soup, el):
        return EdurepExtractor.get_copyright_description(el)


OBJECTIVE = {
    # Essential objective keys for system functioning
    "@": EdurepExtractor.iterate_valid_products,
    "state": EdurepProductExtraction.get_oaipmh_record_state,
    "external_id": EdurepProductExtraction.get_oaipmh_external_id,
    "set": EdurepProductExtraction.get_set,
    # Generic metadata
    "modified_at": EdurepProductExtraction.get_oaipmh_modified_at,
    "files": EdurepProductExtraction.get_files,
    "title": EdurepProductExtraction.get_title,
    "language": EdurepProductExtraction.get_language,
    "keywords": EdurepProductExtraction.get_keywords,
    "description": EdurepProductExtraction.get_description,
    "copyright": EdurepProductExtraction.get_copyright,
    "copyright_description": EdurepProductExtraction.get_copyright_description,
    "authors": EdurepProductExtraction.get_authors,
    "provider": EdurepProductExtraction.get_provider,
    "organizations": EdurepProductExtraction.get_organizations,
    "publishers": EdurepProductExtraction.get_publishers,
    "publisher_date": EdurepProductExtraction.get_publisher_date,
    "publisher_year": EdurepProductExtraction.get_publisher_year,
    # Learning material metadata
    "learning_material.aggregation_level": EdurepProductExtraction.get_aggregation_level,
    "learning_material.material_types": EdurepProductExtraction.get_material_types,
    "learning_material.lom_educational_levels": EdurepProductExtraction.get_educational_levels,
    "learning_material.studies": EdurepProductExtraction.get_studies,
    "learning_material.study_vocabulary": EdurepProductExtraction.get_study_vocabulary,
    "learning_material.disciplines": EdurepProductExtraction.get_studies,
    "learning_material.consortium": EdurepProductExtraction.get_consortium,
}

SEEDING_PHASES = [
    {
        "phase": "publications",
        "strategy": "initial",
        "batch_size": 25,
        "retrieve_data": {
            "resource": "sources.EdurepOAIPMH",
            "method": "get",
            "args": [],
            "kwargs": {},
        },
        "contribute_data": {
            "objective": OBJECTIVE
        }
    }
]

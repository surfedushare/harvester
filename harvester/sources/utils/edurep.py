import logging

import bs4
from vobject.base import ParseError, readOne

from core.constants import HIGHER_EDUCATION_LEVELS, MBO_EDUCATIONAL_LEVELS
from sources.utils.base import BaseExtractor


class EdurepExtractor(BaseExtractor):

    logger = logging.getLogger("harvester")

    #############################
    # HELPERS
    #############################

    @classmethod
    def find_all_classification_blocks(cls, element, classification_type, output_type):
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
    def get_oaipmh_record_state(cls, product):
        """
        Returns the state specified by the record or calculates state based on (non NL-LOM) educational level
        """
        educational_level_state = cls._get_educational_level_state(product)
        header = product.find('header')
        return header.get("status", educational_level_state)

    @classmethod
    def get_educational_levels(cls, product):
        blocks = EdurepExtractor.find_all_classification_blocks(product, "educational level", "czp:entry")
        levels = list(set([block.find('czp:langstring').text.strip() for block in blocks]))
        if product.find('setSpec').text.strip() == "l4l" and len(levels) == 0:
            levels.append("WO")
        return levels

    @classmethod
    def _get_educational_level_state(cls, product):
        """
        Returns the desired state of the record based on (non NL-LOM) educational levels
        """
        educational_levels = cls.get_educational_levels(product)
        if not len(educational_levels):
            return "inactive"
        has_higher_level = False
        has_mbo_level = False
        has_lower_level = False
        for education_level in educational_levels:
            is_higher_level = False
            is_mbo_level = False
            is_lower_level = False
            for higher_education_level in HIGHER_EDUCATION_LEVELS.keys():
                if education_level.startswith(higher_education_level):
                    is_higher_level = True
                    break
            for mbo_education_level in MBO_EDUCATIONAL_LEVELS:
                if education_level.startswith(mbo_education_level):
                    is_mbo_level = True
                    break
            else:
                # The level is not MBO ... so it has to be lower level if it's not higher level
                is_lower_level = not is_higher_level
            # If any education_level matches against higher than HBO or lower than MBO
            # Then we mark the material as higher_level and/or lower_level
            has_higher_level = has_higher_level or is_higher_level
            has_mbo_level = has_mbo_level or is_mbo_level
            has_lower_level = has_lower_level or is_lower_level
        # A record needs to have at least one "higher education" level
        # and should not have any "children education" levels
        return "active" if has_higher_level and not has_lower_level else "inactive"

    @classmethod
    def iterate_valid_products(cls, soup: bs4.BeautifulSoup):
        for product in soup.find_all("record"):
            product_state = cls.get_oaipmh_record_state(product)
            educational_level_state = cls._get_educational_level_state(product)
            if educational_level_state == "inactive" and product_state != "deleted":
                continue
            yield product

    #############################
    # GENERIC TRANSFORMATIONS
    #############################

    @classmethod
    def get_copyright(cls, product):
        node = product.find('czp:copyrightandotherrestrictions')
        if node is None:
            return "yes"
        copyright = node.find('czp:value').find('czp:langstring').text.strip()
        if copyright == "yes":
            copyright = cls.parse_copyright_description(cls.get_copyright_description(product))
        return copyright or "yes"

    @classmethod
    def get_copyright_description(cls, product):
        node = product.find('czp:rights')
        if not node:
            return
        description = node.find('czp:description')
        return description.find('czp:langstring').text.strip() if description else None

    @classmethod
    def parse_vcard_element(cls, record, external_id):
        card = "\n".join(field.strip() for field in record.text.strip().split("\n"))
        try:
            return readOne(card)
        except ParseError:
            cls.logger.warning(f"Can't parse vCard for material with id: {external_id}")
            return

    @classmethod
    def get_publishers(cls, product, external_id):
        publishers = []
        publisher_element = product.find(string='publisher')
        if not publisher_element:
            return publishers
        contribution_element = publisher_element.find_parent('czp:contribute')
        if not contribution_element:
            return publishers
        nodes = contribution_element.find_all('czp:vcard')
        for node in nodes:
            publisher = cls.parse_vcard_element(node, external_id)
            if hasattr(publisher, "fn"):
                publishers.append(publisher.fn.value)
        return publishers

    @classmethod
    def get_provider_name(cls, product, external_id):
        provider_name = None
        publishers = cls.get_publishers(product, external_id)
        if len(publishers):
            provider_name = publishers[0]
        return provider_name

    @classmethod
    def get_provider(cls, product) -> dict | None:
        provider_name = EdurepExtractor.get_provider_name(product, product.find('identifier').text.strip())
        return {
            "ror": None,
            "external_id": None,
            "slug": None,
            "name": provider_name or "Edurep"
        }

from django.conf import settings

from e2e_tests.base import ElasticSearchTestCase
from e2e_tests.elasticsearch_fixtures.elasticsearch import NL_MATERIAL


class TestSearch(ElasticSearchTestCase):
    fixtures = ['filter-categories', 'locales']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.elastic.index(index=settings.ELASTICSEARCH_NL_INDEX, doc_type="_doc", body=NL_MATERIAL)

    def test_search(self):
        self.selenium.get(self.live_server_url)

        search = self.selenium.find_element_by_css_selector(".search.main__info_search input[type=search]")
        button = self.selenium.find_element_by_css_selector(".search.main__info_search button")

        search.send_keys("Wiskunde")
        button.click()

        self.selenium.find_element_by_xpath("//*[text()[contains(., 'Didactiek van wiskundig denken')]]")

    def test_search_by_author(self):
        material_path = f"/materialen/{NL_MATERIAL.get('external_id')}"
        self.selenium.get(f"{self.live_server_url}{material_path}")

        author_link = self.selenium.find_element_by_css_selector(".material__info_author a")
        author_link.click()

        search_results = self.selenium.find_elements_by_css_selector(".materials__item_wrapper.tile__wrapper")
        self.assertEqual(len(search_results), 1)

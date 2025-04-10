from django.test import TestCase

from persons.models import PersonDocument


class PersonDocumentTestCase(TestCase):

    fixtures = ["test-person-document.json"]

    def test_to_search(self):
        person = PersonDocument.objects.get(id=1)
        person_search = person.to_search()
        self.assertEqual(person_search, {
            "set": "hku:person",
            "srn": "hku:person:1",
            "state": "active",
            "skills": [
                "skills-yo"
            ],
            "provider": "Hogeschool voor de Kunsten",
            "job_title": None,
            "external_id": "1",
            "is_employed": None,
            "organizations": [],
            "overwrite": None,
            "metrics": None,
            "dai": None,
            "orcid": "0000-0000-0000-0001",
            "title": "MA",
            "themes": [
                "Taal, Cultuur en Kunsten",
                "Techniek"
            ],
            "isni": None,
            "name": "Pietje Puk",
            "prefix": None,
            "initials": None,
            "last_name": "Puk",
            "first_name": "Pietje",
            "email": "pietje.puk@hku.nl",
            "phone": None,
            "photo_url": "https://octo.hku.nl/octo/repository/getfile?id=FIwGwx6hxCY&version=transcoded",
            "description": "<p>Pietje Puk is a researcher and designer</p>",
            "_id": "hku:person:1",
            "suggest_phrase": "<p>Pietje Puk is a researcher and designer</p>",
            "suggest_completion": [
                "Pietje Puk",
                "pPietje",
                "Puk",
                "is",
                "a",
                "researcher",
                "and",
                "designerp"
            ]
        })

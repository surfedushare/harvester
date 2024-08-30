from django.test import TestCase

from core.utils.analyzers import AnalyzerLanguages
from core.utils.contents import ContentContainer, Content


class TestContentContainer(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.contents = [
            Content(
                srn="test:test:1", provider="test", language=AnalyzerLanguages.ENGLISH,
                title="Test title", description="Test description."
            ),
            Content(
                srn="test:test:2", provider="test", language=AnalyzerLanguages.ENGLISH,
                title="Attachment", description="An attachment."
            ),
            Content(
                srn="test:test:1", provider="test", language=AnalyzerLanguages.DUTCH,
                title="Test titel", description="Test beschrijving"
            ),
            Content(
                srn="test:test:1:1", provider="test", language=AnalyzerLanguages.ENGLISH,
                content="Test content of a file."
            ),
            Content(
                srn="test:test:1:2", provider="youtube", language=AnalyzerLanguages.DUTCH,
                transcription="Test transcriptie van een video.", by_machine=True
            )
        ]

    def test_to_data(self):
        container = ContentContainer(contents=self.contents)
        self.assertEqual(container.to_data(), {
            "en": {
                "contents": [
                    {
                        "text": "Test content of a file.",
                        "document": "test:test:1:1",
                        "provider": "test",
                        "by_machine": False
                    }
                ],
                "descriptions": [
                    {
                        "text": "Test description.",
                        "document": "test:test:1",
                        "provider": "test",
                        "by_machine": False
                    },
                    {
                        "text": "An attachment.",
                        "document": "test:test:2",
                        "provider": "test",
                        "by_machine": False
                    }
                ],
                "transcriptions": [],
                "titles": [
                    {
                        "text": "Test title",
                        "document": "test:test:1",
                        "provider": "test",
                        "by_machine": False
                    },
                    {
                        "text": "Attachment",
                        "document": "test:test:2",
                        "provider": "test",
                        "by_machine": False
                    }
                ],
                "subtitles": []
            },
            "nl": {
                "contents": [],
                "descriptions": [
                    {
                        "text": "Test beschrijving",
                        "document": "test:test:1",
                        "provider": "test",
                        "by_machine": False
                    }
                ],
                "transcriptions": [
                    {
                        "text": "Test transcriptie van een video.",
                        "document": "test:test:1:2",
                        "provider": "youtube",
                        "by_machine": True
                    }
                ],
                "titles": [
                    {
                        "text": "Test titel",
                        "document": "test:test:1",
                        "provider": "test",
                        "by_machine": False
                    }
                ],
                "subtitles": []
            },
            "unk": {
                "contents": [],
                "descriptions": [],
                "transcriptions": [],
                "titles": [],
                "subtitles": []
            }
        })

    def test_container_defaults(self):
        container = ContentContainer(contents=[])
        self.assertEqual(container.to_data(), {
            "en": {
                "descriptions": [],
                "contents": [],
                "titles": [],
                "subtitles": [],
                "transcriptions": []
            },
            "nl": {
                "descriptions": [],
                "contents": [],
                "titles": [],
                "subtitles": [],
                "transcriptions": []
            },
            "unk": {
                "descriptions": [],
                "contents": [],
                "titles": [],
                "subtitles": [],
                "transcriptions": []
            }
        })

    def test_first(self):
        container = ContentContainer(contents=self.contents)
        self.assertEqual(container.first("title"), "Test title")
        self.assertEqual(container.first("description"), "Test description.")
        self.assertEqual(container.first("content"), "Test content of a file.")
        self.assertEqual(container.first("transcription"), "Test transcriptie van een video.")
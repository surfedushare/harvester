from django.core.exceptions import ValidationError

from datagrowth.resources import URLResource


class SkosVocabularyResource(URLResource):

    def clean(self):
        super().clean()
        if not self.uri.endswith("skos.json"):
            raise ValidationError("SKOS Vocabulary Resource should receive a valid SKOS URL.")

from django.test import TestCase

from files.models import YoutubeTranscriptsResource


MOCK_STDOUT = {
    "success": """
################################## Zl59P5ZNX3M.en-qlPKC2UN_YU.vtt ##################################
WEBVTT
Kind: captions
Language: en

00:00:06.400 --> 00:00:09.220
The role of a vortex
is to thoroughly mix

####################################################################################################
    """,
    "invalid_file": """
#################################### dNU0DGrkks8.live_chat.json ####################################
File invalid
####################################################################################################

    """
}


class TestYoutubeTranscriptsResource(TestCase):

    def test_transform(self):
        rsc = YoutubeTranscriptsResource()
        results = rsc.transform(MOCK_STDOUT["success"])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertTrue(result.startswith("WEBVTT"))
        self.assertTrue(result.endswith("is to thoroughly mix"))

    def test_transform_errors(self):
        rsc = YoutubeTranscriptsResource()
        results = rsc.transform(MOCK_STDOUT["invalid_file"])
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

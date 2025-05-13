from django.test import TestCase

from files.models import VideoTranscriptsResource


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


class TestVideoTranscriptsResource(TestCase):

    def test_transform(self):
        rsc = VideoTranscriptsResource()
        result = rsc.transform(MOCK_STDOUT["success"])
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("WEBVTT"))
        self.assertTrue(result.endswith("is to thoroughly mix"))

    def test_transform_errors(self):
        rsc = VideoTranscriptsResource()
        result = rsc.transform(MOCK_STDOUT["invalid_file"])
        self.assertIsInstance(result, str)
        self.assertFalse(result)

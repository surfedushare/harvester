import json
from unittest.mock import patch

from django.test import TestCase

from files.models import HttpTikaResource


class TestTikaResource(TestCase):

    def test_handle_error_with_content_and_exception(self):
        # for now we set the status of the resource to 200 (success)
        # in the future we should finetune this for specific use cases
        expected_data = [
            {
                "http-connection:target-ip-address": "145.97.38.100",
                "http-header:status-code": "200",
                "X-TIKA:Parsed-By-Full-Set": [
                    "org.apache.tika.parser.DefaultParser",
                    "org.apache.tika.parser.pkg.PackageParser",
                    "org.apache.tika.parser.mp4.MP4Parser",
                    "org.apache.tika.parser.EmptyParser"
                ],
                "X-TIKA:content_handler": "ToXMLContentHandler",
                "resourceName": "/file/dcb11873-2a88-4b8b-a771-c26e95f46b60",
                "http-connection:num-redirects": "1",
                "http-connection:target-url": "https://resources.wikiwijs.nl/file/dcb11873-2a88-4b8b-a771-c26e95f46b60",
                "X-TIKA:Parsed-By": [
                    "org.apache.tika.parser.DefaultParser",
                    "org.apache.tika.parser.pkg.PackageParser"
                ],
                "X-TIKA:parse_time_millis": "181",
                "X-TIKA:embedded_depth": "0",
                "X-TIKA:content": "I have content",
                "X-TIKA:EXCEPTION:warn": "Something went wrong",
                "Content-Length": "0",
                "http-header:content-type": "application/zip",
                "Content-Type": "application/zip"
            },
        ]
        expected_content_type = "application/json"
        resource = HttpTikaResource(
            status=200, head={"content-type": expected_content_type}, body=json.dumps(expected_data))
        resource.handle_errors()
        self.assertEqual(resource.status, 200)

    def test_handle_error_without_content_and_without_exception(self):
        expected_data = [
            {
                "http-connection:target-ip-address": "151.101.38.217",
                "http-header:status-code": "200",
                "X-TIKA:Parsed-By-Full-Set": [
                    "org.apache.tika.parser.DefaultParser",
                    "org.apache.tika.parser.html.HtmlParser"
                ],
                "X-TIKA:content_handler": "ToTextContentHandler",
                "resourceName": "apache-tika-14029765778009660889.tmp",
                "http-connection:num-redirects": "0",
                "http-connection:target-url": "https://www.webpagetest.org/blank.html",
                "X-TIKA:Parsed-By": [
                    "org.apache.tika.parser.DefaultParser",
                    "org.apache.tika.parser.html.HtmlParser"
                ],
                "dc:title": "Blank",
                "Content-Encoding": "windows-1252",
                "X-TIKA:parse_time_millis": "165",
                "X-TIKA:embedded_depth": "0",
                "X-TIKA:content": "",
                "Content-Length": "129",
                "http-header:content-type": "text/html",
                "Content-Type": "text/html; charset=windows-1252"
            }
        ]
        expected_content_type = "application/json"
        resource = HttpTikaResource(
            status=200, head={"content-type": expected_content_type}, body=json.dumps(expected_data))
        resource.handle_errors()
        self.assertEqual(resource.status, 204)

    def test_handle_error_without_content_and_with_exception(self):
        # for analyzing and optimization purposes we NOW set the status of the resource to 1 (failed)
        # in the future we should finetune this for specific use cases
        expected_data = [
            {
                "http-connection:target-ip-address": "151.101.38.217",
                "http-header:status-code": "200",
                "X-TIKA:Parsed-By-Full-Set": [
                    "org.apache.tika.parser.DefaultParser",
                    "org.apache.tika.parser.html.HtmlParser"
                ],
                "X-TIKA:content_handler": "ToTextContentHandler",
                "resourceName": "apache-tika-14029765778009660889.tmp",
                "http-connection:num-redirects": "0",
                "http-connection:target-url": "https://www.webpagetest.org/blank.html",
                "X-TIKA:Parsed-By": [
                    "org.apache.tika.parser.DefaultParser",
                    "org.apache.tika.parser.html.HtmlParser"
                ],
                "dc:title": "Blank",
                "Content-Encoding": "windows-1252",
                "X-TIKA:parse_time_millis": "165",
                "X-TIKA:embedded_depth": "0",
                "X-TIKA:content": "",
                "X-TIKA:EXCEPTION:embedded_exception": "This should not happen",
                "Content-Length": "0",
                "http-header:content-type": "text/html",
                "Content-Type": "text/html; charset=windows-1252"
            }
        ]
        expected_content_type = "application/json"
        resource = HttpTikaResource(
            status=200, head={"content-type": expected_content_type}, body=json.dumps(expected_data))
        resource.handle_errors()
        self.assertEqual(resource.status, 1)

    @patch("files.models.resources.metadata.HttpTikaResource._send")
    def test_tika_return_type_configurations(self, send_mock):
        url = "https://example.com/test.pdf"
        plain_resource = HttpTikaResource(config={"tika_return_type": "text"}).put(url)
        self.assertTrue(plain_resource.uri.startswith("tika:9998/rmeta/text"))
        self.assertTrue(plain_resource.request["url"].startswith("http://tika:9998/rmeta/text"))
        xml_resource = HttpTikaResource(config={"tika_return_type": "xml"}).put(url)
        self.assertTrue(xml_resource.uri.startswith("tika:9998/rmeta/xml"))
        self.assertTrue(xml_resource.request["url"].startswith("http://tika:9998/rmeta/xml"))

    @patch("files.models.resources.metadata.HttpTikaResource._send")
    def test_spaces_encoding(self, send_mock):
        url = "https://example.com/test+spaces+encoding.pdf"
        rsc = HttpTikaResource(config={"tika_return_type": "text"}).put(url)
        self.assertTrue(send_mock.called)
        self.assertEqual(
            rsc.uri,
            "tika:9998/rmeta/text?fetchKey="
            "https%3A%2F%2Fexample.com%2Ftest%25252520spaces%25252520encoding.pdf&fetcherName=http"
        )
        self.assertEqual(
            rsc.request["url"],
            "http://tika:9998/rmeta/text?fetcherName=http&fetchKey="
            "https%3A%2F%2Fexample.com%2Ftest%25252520spaces%25252520encoding.pdf"
        )

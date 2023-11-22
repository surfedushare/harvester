import json
import factory

from files.models import CheckURLResource


class CheckURLResourceFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = CheckURLResource

    class Params:
        url = ""
        content_type = "text/html"
        has_redirect = False
        has_temporary_redirect = False

    status = 200
    data_hash = ""

    @factory.lazy_attribute
    def uri(self):
        return CheckURLResource.uri_from_url(self.url)

    @factory.lazy_attribute
    def request(self):
        url = "https://" + self.uri
        return {
            "url": url,
            "args": [self.url],
            "data": {},
            "kwargs": {},
            "method": "head",
            "headers": {
                "Accept": "*/*",
                "Connection": "keep-alive",
                "User-Agent": "DataGrowth (v0.19.0); python-requests/2.31.0",
                "Accept-Encoding": "gzip, deflate"
            },
            "backoff_delay": False
        }

    @factory.lazy_attribute
    def head(self):
        return json.dumps({
            "date": "Fri, 11 Aug 2023 01:27:22 GMT",
            "vary": "Accept-Encoding",
            "server": "Jetty(9.4.49.v20220914)",
            "content-type": "application/json",
            "content-encoding": "gzip",
            "transfer-encoding": "chunked"
        })

    @factory.lazy_attribute
    def body(self):
        return json.dumps({
            "url": self.url,
            "status": self.status,
            "content_type": self.content_type,
            "has_redirect": self.has_redirect,
            "has_temporary_redirect": self.has_temporary_redirect
        })

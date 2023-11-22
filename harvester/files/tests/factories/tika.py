import json
from urllib.parse import quote
import factory

from files.models import HttpTikaResource


class HttpTikaResourceFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = HttpTikaResource

    class Params:
        url = ""
        return_type = "text"

    status = 200
    data_hash = ""

    @factory.lazy_attribute
    def uri(self):
        fetch_key = quote(self.url, safe="")
        return f"tika:9998/rmeta/{self.return_type}?fetchKey={fetch_key}&fetcherName=http"

    @factory.lazy_attribute
    def request(self):
        url = "http://" + self.uri
        return {
            "url": url,
            "args": [self.url],
            "data": {},
            "kwargs": {},
            "method": "put",
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
        if self.status < 200 >= 300:
            return ""
        tika_output = [
            {
                "X-TIKA:content": f"Tika content for {self.url}"
            }
        ]
        return json.dumps(tika_output)

import json
from urllib.parse import quote
import factory

from files.models import YoutubeAPIResource


class HttpYoutubeResourceFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = YoutubeAPIResource

    class Params:
        id = ""
        type = "videos"

    status = 200
    data_hash = ""

    @factory.lazy_attribute
    def uri(self):
        id = quote(self.id, safe="")
        type = quote(self.type, safe="videos")
        return f"youtube.googleapis.com/youtube/v3/{type}?id={id}&part=snippet%2Cplayer%2CcontentDetails%2Cstatus"

    @factory.lazy_attribute
    def request(self):
        url = "http://" + self.uri
        return {
            "url": url,
            "args": [self.id, self.type],
            "data": {},
            "kwargs": {},
            "method": "get",
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
        return json.dumps({'content-type': 'application/json; charset=UTF-8',
                           'vary': 'Origin, X-Origin, Referer',
                           'content-encoding': 'gzip',
                           'date': 'Mon, 09 Oct 2023 11:26:52 GMT',
                           'server': 'scaffolding on HTTPServer2',
                           'cache-control': 'private',
                           'x-xss-protection': '0',
                           'x-frame-options': 'SAMEORIGIN',
                           'x-content-type-options': 'nosniff',
                           'alt-svc': 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000',
                           'transfer-encoding': 'chunked'})

    @factory.lazy_attribute
    def body(self):
        if self.id == "wrongIdHere":
            output = {
                "items": []
            }
            return json.dumps(output)
        id_ = quote(self.id, safe="")
        output = {
            "items": [
                {
                    "kind": "youtube#video",
                    "id": f"{id_}",
                    "snippet": {
                        "publishedAt": "2009-10-25T06:57:33Z",
                        "description": "this is a description",
                        "thumbnails": {
                            "default": {
                                "url": f"https://i.ytimg.com/vi/{id_}/default.jpg",
                            },
                            "medium": {
                                "url": f"https://i.ytimg.com/vi/{id_}/mqdefault.jpg",
                            },
                            "high": {
                                "url": f"https://i.ytimg.com/vi/{id_}/hqdefault.jpg",
                            },
                            "standard": {
                                "url": f"https://i.ytimg.com/vi/{id_}/sddefault.jpg",
                            },
                            "maxres": {
                                "url": f"https://i.ytimg.com/vi/{id_}/maxresdefault.jpg",
                            }
                        }
                    },
                    "contentDetails": {
                        "duration": "PT3M33S",
                        "definition": "hd"
                    },
                    "status": {
                        "license": "youtube",
                    },
                    "player": {
                        "embedHtml": f"<iframe width=\"480\" height=\"270\" src=\"//www.youtube.com/embed/{id_}\" "
                                     f"frameborder=\"0\" allow=\"accelerometer; autoplay; clipboard-write; encryp"
                                     f"ted-media; gyroscope; picture-in-picture; web-share\" allowfullscreen></iframe>"
                    }
                }
            ]
        }
        return json.dumps(output)

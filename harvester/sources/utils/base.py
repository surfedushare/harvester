import re

from django.utils.text import slugify


class BaseExtractor:

    cc_url_regex = re.compile(r"^https?://creativecommons\.org/(?P<type>\w+)/(?P<license>[a-z\-]+)/(?P<version>\d\.\d)",
                              re.IGNORECASE)
    cc_code_regex = re.compile(r"^cc([ \-][a-z]{2})+$", re.IGNORECASE)

    @staticmethod
    def parse_url(url: str) -> str | None:
        if not url:
            return
        url = url.strip()
        url = url.replace(" ", "+")
        url = url.replace("%20", "+")
        return url

    @classmethod
    def parse_copyright_description(cls, description: None | str) -> None | str:
        if description is None:
            return
        elif description == "Public Domain":
            return "pdm-10"
        elif description == "Copyrighted":
            return "yes"
        url_match = cls.cc_url_regex.match(description)
        if url_match is None:
            code_match = cls.cc_code_regex.match(description)
            return slugify(description.lower()) if code_match else None
        license = url_match.group("license").lower()
        if license == "mark":
            license = "pdm"
        elif license == "zero":
            license = "cc0"
        else:
            license = "cc-" + license
        return slugify(f"{license}-{url_match.group('version')}")

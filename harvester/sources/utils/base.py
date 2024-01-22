class BaseExtractor:

    @staticmethod
    def parse_url(url: str) -> str | None:
        if not url:
            return
        url = url.strip()
        url = url.replace(" ", "+")
        return url

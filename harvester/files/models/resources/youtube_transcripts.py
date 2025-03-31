from pathlib import Path
from enum import Enum
from math import floor
from urlobject import URLObject
import logging

from datagrowth.resources import ShellResource


logger = logging.getLogger("harvester")


class YoutubeTranscriptsResource(ShellResource):

    class ErrorCodes(Enum):
        MISSING_FILES = 1
        INVALID_FILES = 2

    CMD_TEMPLATE = [
        "yt-dlp",
        "--sleep-interval", "2",
        "--max-sleep-interval", "5",
        "--skip-download",
        "--all-subs",
        "--output=/tmp/%(id)s",
        "{}"
    ]

    @classmethod
    def _parse_transcription_result(cls, file_path: Path, result: str) -> str:
        title_text = f" {file_path.name} "
        title_size = 100
        margin = floor((title_size - len(title_text)) / 2)
        header = title_text.ljust(margin + len(title_text), "#").rjust(title_size, "#")
        footer = "#" * title_size
        return "\n".join([header, result, footer, "\n"])

    def run(self, *args, **kwargs):
        if "youtu" in args[0]:
            youtube_url = URLObject(args[0])
            youtube_url = youtube_url.del_query_param("list").del_query_param("index")
            args = (str(youtube_url),)
        resource = super().run(*args, **kwargs)
        buffer = ""
        for line in resource.stdout.split("\n"):
            if not line.startswith("[download]") or "/tmp/" not in line:
                continue
            _, file_name = line.split("/tmp/")
            file_path = Path("/tmp/", file_name)
            if not file_path.exists():
                buffer += self._parse_transcription_result(file_path, "File not found")
                resource.status = self.ErrorCodes.MISSING_FILES.value
                continue
            if not file_path.suffix == ".vtt":
                buffer += self._parse_transcription_result(file_path, "File invalid")
                resource.status = self.ErrorCodes.INVALID_FILES.value
                continue
            with file_path.open("r") as transcript_file:
                buffer += self._parse_transcription_result(file_path, transcript_file.read())
        resource.stdout += buffer
        resource.close()
        return resource

    def transform(self, stdout):
        contents = []
        buffer = None
        for line in stdout.split("\n"):
            line = line.strip()
            if line.startswith("WEBVTT"):
                buffer = line + "\n"
            elif line == "#" * 100 and buffer:  # footer line of valid transcript
                contents.append(buffer.strip())
                buffer = None
            elif buffer is not None:
                buffer += line + "\n"
        return contents

    def handle_errors(self):
        # Do not throw an error. We just have a product without transcripts
        # when it is not possible to fetch transcript files.
        return

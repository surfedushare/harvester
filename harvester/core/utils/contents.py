from typing import ClassVar
from dataclasses import dataclass, field
from collections.abc import Iterator

from core.utils.analyzers import AnalyzerLanguages


@dataclass(frozen=True, slots=True)
class Content:
    srn: str
    provider: str
    language: AnalyzerLanguages
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    content: str | None = None
    transcription: str | None = None
    by_machine: bool = False

    def to_data(self, keys: set[str]) -> Iterator[tuple[AnalyzerLanguages, str, dict]]:
        for key in keys:
            if not (text := getattr(self, key, None)):
                continue
            yield self.language, f"{key}s", {
                "text": text,
                "document": self.srn,
                "provider": self.provider,
                "by_machine": self.by_machine,
            }


@dataclass(slots=True)
class ContentContainer:

    contents: list[Content] = field(default_factory=list)
    keys: ClassVar[set[str]] = {"title", "subtitle", "description", "content", "transcription"}

    def append(self, content: Content) -> None:
        self.contents.append(content)

    def first(self, content_key: str) -> str | None:
        if content_key not in self.keys:
            raise ValueError(f"Content key {content_key} not a valid key.")
        for content in self.contents:
            if text := getattr(content, content_key, None):
                return text

    def to_data(self) -> dict:
        data = {
            language.value: {f"{key}s": [] for key in self.keys}
            for language in AnalyzerLanguages

        }
        for content in self.contents:
            for language, key, content_data in content.to_data(self.keys):
                data[language.value][key].append(content_data)
        return data

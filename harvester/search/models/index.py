from __future__ import annotations

from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils.timezone import make_aware
from opensearchpy.helpers import streaming_bulk
from opensearchpy.exceptions import NotFoundError

from search_client.opensearch.configuration import create_open_search_index_configuration
from search.clients import get_opensearch_client


class OpenSearchIndex(models.Model):

    name = models.CharField(max_length=255)
    entity = models.CharField(max_length=50, default="products")
    configuration = models.JSONField(blank=True)
    error_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    pushed_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def build(cls, app_label: str, dataset: str, version: str) -> OpenSearchIndex:
        index = cls(
            entity=app_label,
            name=f"{settings.OPENSEARCH_ALIAS_PREFIX}-{app_label}--{dataset}-{version}"
        )
        index.clean()
        return index

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = get_opensearch_client()

    def delete(self, using=None, keep_parents=False):
        for language in settings.OPENSEARCH_LANGUAGE_CODES:
            if self.check_remote_exists(language):
                self.client.indices.delete(index=self.get_remote_name(language))
        if self.check_remote_exists():
            self.client.indices.delete(index=self.get_remote_name())
        super().delete(using=using, keep_parents=keep_parents)

    def get_remote_name(self, language: str = None) -> str:
        if not self.id:
            raise ValueError("Can't get the remote name for an unsaved object")
        name = self.name
        if language and language != "all":
            name += f"-{language}"
        return name.replace(".", "")

    def get_remote_names(self) -> list[str]:
        names = [
            self.get_remote_name(language)
            for language in settings.OPENSEARCH_LANGUAGE_CODES
        ]
        names.append(self.get_remote_name())
        return names

    def check_remote_exists(self, language: str = None) -> bool:
        if not self.id:
            raise ValueError("Can't check for existence with an unsaved object")
        remote_name = self.get_remote_name(language)
        return self.client.indices.exists(remote_name)

    def push(self, search_documents: dict[str, list[dict]], recreate=True, request_timeout=300) -> list[str]:
        if not self.id:
            raise ValueError("Can't push index with unsaved object")

        current_time = make_aware(datetime.now())
        errors = []
        if recreate:
            self.configuration = {}
            self.error_count = 0
        self.clean()

        for language, documents in search_documents.items():
            # Some preparation based on remote state as well as arguments
            remote_name = self.get_remote_name(language)
            remote_exists = self.check_remote_exists(language)
            if remote_exists and recreate:
                self.client.indices.delete(index=remote_name)
            if remote_exists and recreate or not remote_exists:
                self.client.indices.create(index=remote_name, body=self.configuration[language])
            if recreate:
                documents = [
                    search_document for search_document in documents
                    if search_document.get("_op_type", None) != "delete"
                ]

            # Actual push of docs to ES
            for is_ok, result in streaming_bulk(self.client, documents, index=remote_name,
                                                chunk_size=100, yield_ok=False, raise_on_error=False,
                                                request_timeout=request_timeout):
                if not is_ok:
                    self.error_count += 1
                    errors.append(result)

        self.pushed_at = current_time
        self.save()
        return errors

    def promote_all_to_latest(self) -> None:
        for language in settings.OPENSEARCH_LANGUAGE_CODES:
            self.promote_to_latest(language)

    def promote_to_latest(self, language: str) -> None:
        alias_prefix, dataset_info = self.name.split("--")
        alias = f"{alias_prefix}-{language}"
        legacy_alias = f"{settings.OPENSEARCH_ALIAS_PREFIX}-{language}"
        # The index pattern should target all datasets and versions,
        # but stay clear from deleting cross project and cross language indices to prevent data loss
        # as well as targeting protected AWS indices to prevent errors
        index_pattern = f"{alias_prefix}--*-*-{language}"
        legacy_pattern = f"*-*-*-{settings.OPENSEARCH_ALIAS_PREFIX}-{language}"
        try:
            self.client.indices.delete_alias(index=index_pattern, name=alias)
            self.client.indices.delete_alias(index=index_pattern, name=legacy_alias)
        except NotFoundError:
            pass
        if self.check_remote_exists(language):
            self.client.indices.put_alias(index=self.get_remote_name(language), name=alias)
            self.client.indices.put_alias(index=self.get_remote_name(language), name=legacy_alias)
            try:
                self.client.indices.delete_alias(index=legacy_pattern, name=legacy_alias)
            except NotFoundError:
                pass

    def clean(self) -> None:
        if not self.configuration:
            self.configuration = {
                language: self.get_index_config(language)
                for language in settings.OPENSEARCH_LANGUAGE_CODES
            }
            self.configuration["all"] = self.get_index_config()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "OpenSearch index"
        verbose_name_plural = "OpenSearch indices"

    @staticmethod
    def get_index_config(language: str = None) -> dict:
        """
        Returns the elasticsearch index configuration.
        Configures the analysers based on the language passed in.
        """
        decompound_word_list = None
        if settings.OPENSEARCH_ENABLE_DECOMPOUND_ANALYZERS:
            decompound_word_list = settings.OPENSEARCH_DECOMPOUND_WORD_LISTS.dutch
        if language is None:
            return create_open_search_index_configuration(
                "unk",
                settings.DOCUMENT_TYPE,
                decompound_word_list=decompound_word_list
            )
        return create_open_search_index_configuration(
            language,
            settings.DOCUMENT_TYPE,
            decompound_word_list=decompound_word_list
        )

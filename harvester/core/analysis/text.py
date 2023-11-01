from re import split
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer


def get_document_texts(queryset, keys=None, unpack=None, singles=None):
    keys = keys or []
    unpack = set(unpack) if unpack else set()
    singles = set(singles) if singles else set()
    assert not unpack.intersection(singles), \
        "The keys to unpack should not overlap with keys to get single values from " \
        "as these operations are mutaly exclusie"

    texts = []
    for document in queryset.iterator():
        data = document.to_data()
        for key in keys:
            value = data.get(key)
            if key in unpack:
                value = value or []
                texts += value
            elif key in singles:
                if not value or not isinstance(value, list):
                    continue
                value = value[0] or ""
                texts.append(value)
            else:
                value = value or ""
                texts.append(value)

    return texts


def build_document_word_count(queryset, keys=None, unpack=None, singles=None):
    texts = get_document_texts(queryset, keys=keys, unpack=unpack, singles=singles)
    words = []
    for text in texts:
        words += split(r"\W+", text)
    return Counter(word.lower() for word in words)


def build_document_vectorizer(queryset, keys=None, unpack=None, singles=None, count=None, tfidf=None, as_counter=False):
    count = count or {}
    if tfidf and isinstance(tfidf, bool):
        tfidf_options = {}
    else:
        tfidf_options = tfidf or {}

    texts = get_document_texts(queryset, keys=keys, unpack=unpack, singles=singles)
    if tfidf:
        vectorizer = TfidfVectorizer(**tfidf_options)
        vectors = vectorizer.fit_transform(texts)
    else:
        vectorizer = CountVectorizer(**count)
        vectors = vectorizer.fit_transform(texts)

    if as_counter:
        values = np.asarray(vectors.sum(axis=0))
        return Counter(**dict(zip(vectorizer.get_feature_names_out(), values[0])))
    return vectorizer

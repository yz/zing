# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
# Copyright (C) Zing contributors.
#
# This file is a part of the Zing project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

import Levenshtein

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ElasticsearchException
except ImportError:
    Elasticsearch = None

from ..base import SearchBackend


__all__ = ("ElasticSearchBackend",)


logger = logging.getLogger(__name__)


DEFAULT_MIN_SIMILARITY = 0.7
INDEX_PREFIX = "zing_tm_"


def filter_hits_by_distance(hits, source_text, min_similarity=DEFAULT_MIN_SIMILARITY):
    """Returns ES `hits` filtered according to their Levenshtein distance
    to the `source_text`.

    Any hits with a similarity value (0..1) lower than `min_similarity` will be
    discarded. It's assumed that `hits` is already sorted from higher to lower
    score.
    """
    if min_similarity <= 0 or min_similarity >= 1:
        min_similarity = DEFAULT_MIN_SIMILARITY

    filtered_hits = []
    for hit in hits:
        hit_source_text = hit["_source"]["source"]
        distance = Levenshtein.distance(source_text, hit_source_text)
        similarity = 1 - distance / float(max(len(source_text), len(hit_source_text)))

        logger.debug(
            "Similarity: %.2f (distance: %d)\nOriginal:\t%s\nComparing with:\t%s",
            similarity,
            distance,
            source_text,
            hit_source_text,
        )

        if similarity < min_similarity:
            break

        filtered_hits.append(hit)

    return filtered_hits


class ElasticSearchBackend(SearchBackend):
    def __init__(self):
        super().__init__()
        self._es = self._get_es_server()

    def _get_es_server(self):
        return Elasticsearch(
            [{"host": self._settings["HOST"], "port": self._settings["PORT"]}]
        )

    def _create_index_if_missing(self, name):
        try:
            if not self._es.indices.exists(name):
                self._es.indices.create(name)
        except ElasticsearchException as e:
            self._log_error(e)

    def _is_valuable_hit(self, unit, hit):
        return str(unit.id) != hit["_id"]

    def _es_call(self, cmd, *args, **kwargs):
        try:
            return getattr(self._es, cmd)(*args, **kwargs)
        except ElasticsearchException as e:
            self._log_error(e)
            return None

    def _log_error(self, e):
        logger.error(
            "Elasticsearch error for server(%s:%s): %s",
            self._settings.get("HOST"),
            self._settings.get("PORT"),
            e,
        )

    def search(self, unit):
        counter = {}
        res = []
        language = unit.store.translation_project.language.code
        index_name = INDEX_PREFIX + language.lower()
        es_res = self._es_call(
            "search",
            index=index_name,
            body={
                "query": {
                    "match": {"source": {"query": unit.source, "fuzziness": "AUTO"}}
                }
            },
        )

        if es_res is None:
            # ElasticsearchException - eg ConnectionError.
            return []
        elif es_res == "":
            # There seems to be an issue with urllib where an empty string is
            # returned
            logger.error(
                "Elasticsearch search (%s:%s) returned an empty " "string: %s",
                self._settings["HOST"],
                self._settings["PORT"],
                unit,
            )
            return []

        hits = filter_hits_by_distance(
            es_res["hits"]["hits"],
            unit.source,
            min_similarity=self._settings.get("MIN_SIMILARITY", DEFAULT_MIN_SIMILARITY),
        )
        for hit in hits:
            if self._is_valuable_hit(unit, hit):
                body = hit["_source"]
                translation_pair = body["source"] + body["target"]
                if translation_pair not in counter:
                    counter[translation_pair] = 1
                    res.append(
                        {
                            "unit_id": hit["_id"],
                            "source": body["source"],
                            "target": body["target"],
                            "project": body["project"],
                            "path": body["path"],
                            "username": body["username"],
                            "fullname": body["fullname"],
                            "email_md5": body["email_md5"],
                            "mtime": body.get("mtime", None),
                            "score": hit["_score"],
                        }
                    )
                else:
                    counter[translation_pair] += 1

        for item in res:
            item["count"] = counter[item["source"] + item["target"]]

        return res

    def update(self, language, obj):
        index_name = INDEX_PREFIX + language.lower()
        self._create_index_if_missing(index_name)
        self._es_call("index", index=index_name, body=obj, id=obj["id"])

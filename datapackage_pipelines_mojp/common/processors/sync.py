import json
from elasticsearch import Elasticsearch, NotFoundError
from datapackage_pipelines_mojp.common.processors.base_processors import FilterResourcesProcessor
from datapackage_pipelines_mojp.settings import temp_loglevel, logging
from datapackage_pipelines_mojp.common.constants import (ALL_KNOWN_COLLECTIONS, COLLECTION_UNKNOWN,
                                                         SLUG_LANGUAGES_MAP, SUPPORTED_SUGGEST_LANGS)
import iso639
from copy import deepcopy
import logging
from slugify import Slugify

COLLECTION_FIELD_DESCRIPTION = "standard collection identifier (e.g. places / familyNames etc..). " \
                               "must be related to one of the COLLECTION_? constants"


DBS_DOCS_TABLE_SCHEMA = {"fields": [{"name": "source", "type": "string"},
                                    {'name': 'id', 'type': 'string'},
                                    {"name": "version", "type": "string",
                                     "description": "source dependant field, used by sync process to detect document updates"},
                                    {"name": "collection", "type": "string",
                                        "description": COLLECTION_FIELD_DESCRIPTION},
                                    {"name": "source_doc", "type": "object"},
                                    {"name": "title", "type": "object",
                                    "description": "languages other then he/en, will be flattened on elasticsearch to content_html_LANG"},
                                    {"name": "title_he", "type": "string"},
                                    {"name": "title_en", "type": "string"},
                                    {"name": "content_html", "type": "object",
                                     "description": "languages other then he/en, will be flattened on elasticsearch to content_html_LANG"},
                                    {"name": "content_html_he", "type": "string"},
                                    {"name": "content_html_en", "type": "string"},
                                    {"name": "main_image_url", "type": "string",
                                     "description": "url to the main image"},
                                    {"name": "main_thumbnail_image_url", "type": "string",
                                     "description": "url to the main thumbnail image"},]}

DBS_DOCS_SYNC_LOG_TABLE_SCHAME = {"fields": [{"name": "source", "type": "string"},
                                             {'name': 'id', 'type': 'string'},
                                             {"name": "version", "type": "string",
                                              "description": "source dependant field, used by sync process to detect document updates"},
                                             {"name": "collection", "type": "string",
                                                 "description": COLLECTION_FIELD_DESCRIPTION},
                                             {"name": "sync_msg", "type": "string"}]}

INPUT_RESOURCE_NAME = "dbs_docs"
OUTPUT_RESOURCE_NAME = "dbs_docs_sync_log"


class CommonSyncProcessor(FilterResourcesProcessor):

    def __init__(self, *args, **kwargs):
        super(CommonSyncProcessor, self).__init__(*args, **kwargs)
        self._es = Elasticsearch(self._get_settings("MOJP_ELASTICSEARCH_DB"))
        self._idx = self._get_settings("MOJP_ELASTICSEARCH_INDEX")

    def _filter_resource_descriptor(self, descriptor):
        if descriptor["name"] == INPUT_RESOURCE_NAME:
            descriptor.update({"name": OUTPUT_RESOURCE_NAME,
                               "path": "{}.csv".format(OUTPUT_RESOURCE_NAME),
                               "schema": DBS_DOCS_SYNC_LOG_TABLE_SCHAME})
        return descriptor

    def _get_sync_response(self, doc, sync_msg):
        return {"source": doc["source"], "id": doc.get("source_id", doc.get("id")), "version": doc["version"],
                "collection": doc["collection"], "sync_msg": sync_msg}

    def _add_doc(self, new_doc):
        with temp_loglevel(logging.ERROR):
            self._es.index(index=self._idx, doc_type=self._get_settings(
                "MOJP_ELASTICSEARCH_DOCTYPE"), body=new_doc, id="{}_{}".format(new_doc["source"], new_doc["source_id"]))
        return self._get_sync_response(new_doc, "added to ES")

    def _update_doc(self, new_doc, old_doc):
        if old_doc["version"] != new_doc["version"]:
            self._update_doc_slugs(new_doc, old_doc)
            with temp_loglevel(logging.ERROR):
                self._es.index(index=self._idx, doc_type="common",
                                id="{}_{}".format(
                                    new_doc["source"], new_doc["source_id"]),
                                body=new_doc)
            return self._get_sync_response(new_doc, "updated doc in ES (old version = {})".format(json.dumps(old_doc["version"])))
        else:
            return self._get_sync_response(new_doc, "no update needed")

    def _update_doc_slugs(self, new_doc, old_doc):
        # aggregate the new and old doc slugs - so that we will never delete any existing slugs, only add new ones
        for lang in iso639.languages.part1:
            old_slug = old_doc["slug_{}".format(lang)] if "slug_{}".format(lang) in old_doc else None
            if old_slug:
                new_slug = new_doc["slug_{}".format(lang)] if "slug_{}".format(lang) in new_doc else None
                if new_slug:
                    new_slug = [new_slug] if isinstance(new_slug, str) else new_slug
                    old_slug = [old_slug] if isinstance(old_slug, str) else old_slug
                    for s in old_slug:
                        if s not in new_slug:
                            new_slug.append(s)
                    if len(new_slug) == 1:
                        new_slug = new_slug[0]
                    new_doc["slug_{}".format(lang)] = new_slug
                else:
                    new_doc["slug_{}".format(lang)] = old_slug
        # aggregate the slugs field which contains slugs from all languages
        if "slugs" in old_doc:
            for slug in old_doc["slugs"]:
                if slug not in new_doc["slugs"]:
                    new_doc["slugs"].append(slug)

    def _filter_row(self, row, resource_descriptor):
        if resource_descriptor["name"] == "dbs_docs_sync_log":
            pre_validate_response = self._pre_validate_row(row)
            if pre_validate_response:
                logging.info("skipping invalid row ({source}:{collection},{id}@{version}".format(
                    source=row.get("source"), collection=row.get("collection"),
                    version=row.get("version"), id=row.get("id")))
                pre_validate_response["sync_msg"] = "not synced ({})".format(pre_validate_response["sync_msg"])
                return pre_validate_response
            else:
                logging.info("processing row ({source}:{collection},{id}@{version}".format(
                    source=row.get("source"), collection=row.get("collection"),
                    version=row.get("version"), id=row.get("id")))
                original_row = deepcopy(row)
                try:
                    row = deepcopy(original_row)
                    source_doc = row.pop("source_doc")
                    new_doc = self._initialize_new_doc(row, source_doc)
                    self._populate_language_fields(new_doc, row)
                    self._add_title_related_fields(new_doc)
                    self._validate_collection(new_doc)
                    self._validate_slugs(new_doc)
                    with temp_loglevel(logging.ERROR):
                        try:
                            old_doc = self._es.get(index=self._idx, id="{}_{}".format(
                                new_doc["source"], new_doc["source_id"]))["_source"]
                        except NotFoundError:
                            old_doc = None
                    if old_doc:
                        return self._update_doc(new_doc, old_doc)
                    else:
                        return self._add_doc(new_doc)
                except Exception:
                    logging.exception("unexpected exception, "
                                      "resource_descirptor={0}, "
                                      "row={1}".format(resource_descriptor,
                                                       original_row))
                    raise
        else:
            return row

    def _pre_validate_row(self, row):
        content_html_he = row.get("content_html_he", "")
        content_html_en = row.get("content_html_en", "")
        if ((content_html_he is None or len(content_html_he) < 1)
            and (content_html_en is None or len(content_html_en) < 1)):
            return self._get_sync_response(row, "missing content in en and he")
        return None

    def _validate_collection(self, new_doc):
        if "collection" not in new_doc or new_doc["collection"] not in ALL_KNOWN_COLLECTIONS:
            new_doc["collection"] = COLLECTION_UNKNOWN

    def _initialize_new_doc(self, row, source_doc):
        # the source doc is used as the base for the final es doc
        # but, we make sure all attributes are strings to ensure we don't have wierd values there (we have)
        new_doc = {}
        for k, v in source_doc.items():
            new_doc[k] = str(v)
        # then, we override with the other row values
        new_doc.update(row)
        # rename the id field
        new_doc["source_id"] = str(new_doc.pop("id"))
        return new_doc

    def _add_slug(self, new_doc, title, lang):
        if title:
            collection = new_doc.get("collection", "")
            slug_parts = []
            if collection in SLUG_LANGUAGES_MAP:
                if lang in SLUG_LANGUAGES_MAP[collection]:
                    slug_collection = SLUG_LANGUAGES_MAP[collection][lang]
                else:
                    slug_collection = SLUG_LANGUAGES_MAP[collection]["en"]
            else:
                slug_collection = None
            if new_doc["source"] != "clearmash" or slug_collection is None or lang not in ["en", "he"]:
                slug_parts.append(new_doc["source"])
            if slug_collection:
                slug_parts.append(slug_collection)
            slug_parts.append(title.lower())
            slugify = Slugify(translate=None, safe_chars='_')
            slug = slugify(u'_'.join([p.replace("_", "-") for p in slug_parts]))
            new_doc["slug_{}".format(lang)] = slug

    def _validate_slugs(self, new_doc):
        # all unique slugs for all languages
        slugs = []
        for lang in iso639.languages.part1:
            if "slug_{}".format(lang) in new_doc:
                slug = new_doc["slug_{}".format(lang)]
                if slug not in slugs:
                    slugs.append(slug)
        # ensure every doc has at least 1 slug (in any language)
        if len(slugs) == 0:
            # add english slug comprised of doc id
            self._add_slug(new_doc, new_doc["source_id"], "en")
            slugs.append(new_doc["slug_en"])
        # add the slugs attribute (needed for fetching item page based on slug)
        new_doc["slugs"] = slugs

    def _add_title_related_fields(self, new_doc):
        for lang in iso639.languages.part1:
            if "title_{}".format(lang) in new_doc:
                title = new_doc["title_{}".format(lang)]
                # lower-case title
                new_doc["title_{}_lc".format(lang)] = title.lower() if title is not None else ""
                # slug
                self._add_slug(new_doc, title, lang)
        # ensure there is a value for all suggest supported langs
        for lang in SUPPORTED_SUGGEST_LANGS:
            val = new_doc.get("title_{}".format(lang), "")
            if val is None or len(val) < 1:
                val = "_"
            new_doc["title_{}_suggest".format(lang)] = val

    def _populate_language_fields(self, new_doc, row):
        for lang_field in ["title", "content_html"]:
            if row[lang_field]:
                for lang, value in row[lang_field].items():
                    if lang in iso639.languages.part1:
                        new_doc["{}_{}".format(
                            lang_field, lang)] = value
                    else:
                        raise Exception(
                            "language identifier not according to iso639 standard: {}".format(lang))
            # delete the combined json lang field from the new_doc
            del new_doc[lang_field]


if __name__ == '__main__':
    CommonSyncProcessor.main()

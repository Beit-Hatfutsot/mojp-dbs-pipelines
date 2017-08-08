import json
from elasticsearch import NotFoundError
from datapackage_pipelines_mojp.common.processors.base_processors import BaseProcessor
from datapackage_pipelines_mojp.settings import temp_loglevel
from datapackage_pipelines_mojp.common import constants
from datapackage_pipelines_mojp.common.utils import get_elasticsearch
import iso639
from copy import deepcopy
import logging
from slugify import Slugify


class CommonSyncProcessor(BaseProcessor):

    def __init__(self, *args, **kwargs):
        super(CommonSyncProcessor, self).__init__(*args, **kwargs)
        self._es, self._idx = get_elasticsearch(self._settings)

    @classmethod
    def _get_schema(cls):
        return constants.DBS_DOCS_SYNC_LOG_TABLE_SCHEMA

    def _filter_row(self, row):
        if not self._pre_validate_row(row):
            self._warn_once("rows are skipped because they failed pre validation")
            return None
        else:
            logging.info("{source}:{collection},{id}@{version}".format(
                source=row.get("source"), collection=row.get("collection"),
                version=row.get("version"), id=row.get("id")))
            original_row = deepcopy(row)
            try:
                row = deepcopy(original_row)
                source_doc = row.pop("source_doc")
                new_doc = self._initialize_new_doc(row, source_doc)
                self._populate_language_fields(new_doc, row)
                self._populate_related_documents(new_doc, row)
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
                logging.exception("unexpected exception, row={}".format(original_row))
                raise

    def _get_sync_response(self, doc, sync_msg):
        return {"source": doc["source"], "id": doc.get("source_id", doc.get("id")), "version": doc["version"],
                "collection": doc["collection"], "sync_msg": sync_msg}

    def _add_doc(self, new_doc):
        with temp_loglevel(logging.ERROR):
            self._es.index(index=self._idx, doc_type=constants.PIPELINES_ES_DOC_TYPE,
                           body=new_doc, id="{}_{}".format(new_doc["source"], new_doc["source_id"]))
        return self._get_sync_response(new_doc, "added to ES")

    def _update_doc(self, new_doc, old_doc):
        if old_doc["version"] == new_doc["version"]:
            self._warn_once("rows are updated even though version is the same")
        self._update_doc_slugs(new_doc, old_doc)
        with temp_loglevel(logging.ERROR):
            self._es.index(index=self._idx, doc_type=constants.PIPELINES_ES_DOC_TYPE,
                            id="{}_{}".format(new_doc["source"], new_doc["source_id"]),
                            body=new_doc)
        return self._get_sync_response(new_doc, "updated doc in ES")


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

    def _pre_validate_row(self, row):
        content_html_he = row.get("content_html_he", "")
        content_html_en = row.get("content_html_en", "")
        if ((content_html_he is not None and len(content_html_he) > 0)
            or (content_html_en is not None and len(content_html_en) > 0)):
            return True
        else:
            self._warn_once("rows are skipped because they are missing content_html in hebrew or english (or both)")
            return False

    def _validate_collection(self, new_doc):
        if "collection" not in new_doc or new_doc["collection"] not in constants.ALL_KNOWN_COLLECTIONS:
            new_doc["collection"] = constants.COLLECTION_UNKNOWN
            self._warn_once("rows get collection=unknown because they don't have a collection or the collection is unknown")

    def _initialize_new_doc(self, row, source_doc):
        # the source doc is used as the base for the final es doc
        # but, we make sure all attributes are strings to ensure we don't have wierd values there (we have)
        new_doc = {}
        for k, v in source_doc.items():
            if isinstance(v, dict):
                new_doc[k] = json.dumps(v)
            else:
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
            if collection in constants.SLUG_LANGUAGES_MAP:
                if lang in constants.SLUG_LANGUAGES_MAP[collection]:
                    slug_collection = constants.SLUG_LANGUAGES_MAP[collection][lang]
                else:
                    slug_collection = constants.SLUG_LANGUAGES_MAP[collection]["en"]
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
                slug = self._ensure_slug_uniqueness(slug, new_doc)
                new_doc["slug_{}".format(lang)] = slug
                if slug not in slugs:
                    slugs.append(slug)
        # ensure every doc has at least 1 slug (in any language)
        if len(slugs) == 0:
            # add english slug comprised of doc id
            self._warn_once("docs are added a default slug (probably due to missing title)")
            self._add_slug(new_doc, new_doc["source_id"], "en")
            slug = new_doc["slug_en"]
            slug = self._ensure_slug_uniqueness(slug, new_doc)
            new_doc["slug_en"] = slug
            slugs.append(slug)
        # add the slugs attribute (needed for fetching item page based on slug)
        new_doc["slugs"] = slugs

    def _ensure_slug_uniqueness(self, slug, doc):
        body = {"query": {"constant_score": {"filter": {"term": {"slugs": slug}}}}}
        results = self._es.search(index=self._idx, doc_type=constants.PIPELINES_ES_DOC_TYPE, body=body, ignore_unavailable=True)
        for hit in results["hits"]["hits"]:
            if hit["_id"] != "{}_{}".format(doc["source"], doc["source_id"]):
                return self._ensure_slug_uniqueness("{}-{}".format(slug, doc["source_id"]), doc)
        return slug

    def _add_title_related_fields(self, new_doc):
        for lang in iso639.languages.part1:
            if "title_{}".format(lang) in new_doc:
                title = new_doc["title_{}".format(lang)]
                # lower-case title
                new_doc["title_{}_lc".format(lang)] = title.lower() if title is not None else ""
                # slug
                self._add_slug(new_doc, title, lang)
        # ensure there is a value for all suggest supported langs
        for lang in constants.SUPPORTED_SUGGEST_LANGS:
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

    def _populate_related_documents(self, new_doc, row):
        if "related_documents" in new_doc:
            for k, v in new_doc["related_documents"].items():
                new_doc["related_documents_{}".format(k)] = v
            del new_doc["related_documents"]

if __name__ == '__main__':
    CommonSyncProcessor.main()

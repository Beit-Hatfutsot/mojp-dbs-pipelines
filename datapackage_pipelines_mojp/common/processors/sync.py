import json
from elasticsearch import Elasticsearch, NotFoundError
from datapackage_pipelines_mojp.common.processors.base_processors import FilterResourcesProcessor
from datapackage_pipelines_mojp.settings import temp_loglevel, logging
from datapackage_pipelines_mojp.common.constants import ALL_KNOWN_COLLECTIONS, COLLECTION_UNKNOWN
import iso639
from copy import deepcopy
import logging

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

    def _add_doc(self, new_doc):
        with temp_loglevel(logging.ERROR):
            self._es.index(index=self._idx, doc_type=self._get_settings(
                "MOJP_ELASTICSEARCH_DOCTYPE"), body=new_doc, id="{}_{}".format(new_doc["source"], new_doc["source_id"]))
        return {"source": new_doc["source"], "id": new_doc["source_id"], "version": new_doc["version"],
                "collection": new_doc["collection"], "sync_msg": "added to ES"}

    def _update_doc(self, new_doc, old_doc):
        if old_doc["version"] != new_doc["version"]:
            with temp_loglevel(logging.ERROR):
                self._es.update(index=self._idx, doc_type="common",
                                id="{}_{}".format(
                                    new_doc["source"], new_doc["source_id"]),
                                body={"doc": new_doc})
            return {"source": new_doc["source"], "id": new_doc["source_id"], "version": new_doc["version"],
                    "collection": new_doc["collection"],
                    "sync_msg": "updated doc in ES (old version = {})".format(json.dumps(old_doc["version"]))}
        else:
            return {"source": new_doc["source"], "id": new_doc["source_id"], "version": new_doc["version"],
                    "collection": new_doc["collection"],
                    "sync_msg": "no update needed"}

    def _filter_row(self, row, resource_descriptor):
        if resource_descriptor["name"] == "dbs_docs_sync_log":
            logging.info("processing row ({source}:{collection},{id}@{version}".format(source=row.get("source"),
                                                                                       collection=row.get(
                                                                                           "collection"),
                                                                                       version=row.get(
                                                                                           "version"),
                                                                                       id=row.get("id")))
            original_row = deepcopy(row)
            try:
                row = deepcopy(original_row)
                source_doc = row.pop("source_doc")
                # the source doc is used as the base for the final es doc
                # but, we make sure all attributes are strings to ensure we don't have wierd values there (we have)
                new_doc = {}
                for k, v in source_doc.items():
                    new_doc[k] = str(v)
                # then, we override with the other row values
                new_doc.update(row)
                # rename the id field
                new_doc["source_id"] = str(new_doc.pop("id"))
                # populate the language fields
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
                # lower-case title
                for lang in iso639.languages.part1:
                    if "title_{}".format(lang) in new_doc:
                        title = new_doc["title_{}".format(lang)]
                        new_doc["title_{}_lc"] = title.lower() if title is not None else ""
                # ensure collection attribute is correct
                if "collection" not in new_doc or new_doc["collection"] not in ALL_KNOWN_COLLECTIONS:
                    new_doc["collection"] = COLLECTION_UNKNOWN
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
        return row


if __name__ == '__main__':
    CommonSyncProcessor.main()

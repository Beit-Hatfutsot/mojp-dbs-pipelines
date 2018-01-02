from datapackage_pipelines.wrapper import ingest, spew
from datapackage_pipelines_mojp.clearmash.api import ClearmashApi, parse_clearmash_documents
from datapackage_pipelines.utilities.resources import PROP_STREAMING
from datapackage_pipelines_mojp.clearmash.constants import TEMPLATE_ID_COLLECTION_MAP
from datapackage_pipelines_mojp.clearmash.common import doc_show_filter
import logging


parameters, datapackage, resources = ingest()


DEFAULT_PARAMETERS = {}
parameters = dict(DEFAULT_PARAMETERS, **parameters)
stats = {"total downloaded": 0, "not allowed": 0, "allowed": 0, "failed download": 0}
aggregations = {"stats": stats, "error_entity_ids": set()}


api = ClearmashApi()


entity_ids_descriptor, entity_ids_resource = None, None
for descriptor, resource in zip(datapackage["resources"], resources):
    if descriptor["name"] == "entity-ids":
        entity_ids_descriptor, entity_ids_resource = descriptor, resource
    else:
        raise Exception("unexpected resource {}".format(descriptor["name"]))


def get_entities(entity_id_rows):
    entity_ids = [row["id"] for row in entity_id_rows]
    try:
        for doc in parse_clearmash_documents(api.get_documents(entity_ids)):
            doc.update(collection=TEMPLATE_ID_COLLECTION_MAP.get(doc["template_id"], "unknown"),
                       display_allowed=doc_show_filter(doc["parsed_doc"]))
            stats["total downloaded"] += 1
            if doc["display_allowed"]:
                stats["allowed"] += 1
            else:
                stats["not allowed"] += 1
            doc.update(**[row for row in entity_id_rows if row["id"] == doc["item_id"]][0])
            yield doc
    except Exception:
        if len(entity_id_rows) < 2:
            raise
        else:
            logging.exception("failed to get entity ids {}".format(entity_ids))
            logging.info("will try one by one")
            for entity_id_row in entity_id_rows:
                try:
                    docs = list(get_entities([entity_id_row]))
                    assert len(docs) == 1
                    yield docs[0]
                except Exception:
                    aggregations["error_entity_ids"].add(int(entity_id_row["id"]))
                    stats["failed download"] += 1


def get_resource():
    rows_queue = []
    for row in entity_ids_resource:
        if not row["is_folder"]:
            rows_queue.append(row)
        if len(rows_queue) > 10:
            yield from get_entities(rows_queue)
            rows_queue = []
    if len(rows_queue) > 0:
        yield from get_entities(rows_queue)


def get_failed_entity_ids_resource():
    for entity_id in aggregations["error_entity_ids"]:
        yield {"entity_id": entity_id}


entity_ids_descriptor.update(name="entities", path="entities.csv")
entity_ids_descriptor["schema"]["fields"] += [{"name": "document_id", "type": "string",
                                               "description": "some sort of internal GUID"},
                                              {"name": "item_id", "type": "integer",
                                               "description": "the item id as requested from the folder"},
                                              {"name": "item_url", "type": "string",
                                               "description": "url to view the item in CM"},
                                              {"name": "collection", "type": "string",
                                               "description": "common dbs docs collection string"},
                                              {"name": "template_changeset_id", "type": "integer",
                                               "description": "I guess it's the id of template when doc was saved"},
                                              {"name": "template_id", "type": "string",
                                               "description": "can help to identify the item type"},
                                              {"name": "changeset", "type": "integer",
                                               "description": ""},
                                              {"name": "metadata", "type": "object",
                                               "description": "full metadata"},
                                              {"name": "parsed_doc", "type": "object",
                                               "description": "all other attributes"},
                                              {"name": "display_allowed", "type": "boolean"}]
failed_entity_ids_descriptor = {PROP_STREAMING: True,
                                "name": "failed-entity-ids",
                                "path": "failed-entity-ids.csv",
                                "schema": {"fields": [{"name": "entity_id", "type": "integer"}]}}
spew(dict(datapackage, resources=[entity_ids_descriptor, failed_entity_ids_descriptor]),
     [get_resource(), get_failed_entity_ids_resource()], aggregations["stats"])

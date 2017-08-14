import logging, os
from datapackage_pipelines_mojp.clearmash.processors.download import CLEARMASH_DOWNLOAD_SCHEMA
from datapackage_pipelines_mojp.clearmash.processors.add_entity_ids import Processor as AddEntityIdsProcesor
from datapackage_pipelines_mojp.common.constants import GEOCODE_LOCATION_SCHEMA


def get_override_item_ids_where():
    override_ids = os.environ.get("OVERRIDE_CLEARMASH_ITEM_IDS")
    if override_ids:
        override_ids = override_ids.split(",")
        where = "item_id in ({})".format(",".join(["'{}'".format(id) for id in override_ids]))
        logging.info("where {}".format(where))
        return where
    else:
        return None


def entities_sync_where():
    where = "(last_synced IS NULL or last_downloaded > last_synced)"
    item_ids_where = get_override_item_ids_where()
    if item_ids_where:
        where = "{} and {}".format(where, item_ids_where)
    return where


def entities_schema():
    return CLEARMASH_DOWNLOAD_SCHEMA


def entity_ids_schema():
    return AddEntityIdsProcesor._get_schema()

def geocode_location_schema():
    return GEOCODE_LOCATION

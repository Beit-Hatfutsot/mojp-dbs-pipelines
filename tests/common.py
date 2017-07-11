import os
from datapackage_pipelines_mojp.common.processors.sync import (DBS_DOCS_TABLE_SCHEMA, CommonSyncProcessor,
                                                               DBS_DOCS_SYNC_LOG_TABLE_SCHAME,
                                                               OUTPUT_RESOURCE_NAME as DBS_DOCS_SYNC_LOG_RESOURCE_NAME,
                                                               INPUT_RESOURCE_NAME as DBS_DOCS_RESOURCE_NAME)
from jsontableschema.model import SchemaModel
from jsontableschema import Schema
from elasticsearch import Elasticsearch, NotFoundError
import json, logging
from datapackage_pipelines_mojp.common.constants import COLLECTION_PLACES, COLLECTION_FAMILY_NAMES
from datapackage_pipelines_mojp.clearmash.constants import CLEARMASH_SOURCE_ID
from copy import deepcopy

ROOT_PATH = os.path.join(os.path.dirname(__file__), '..')
ELASTICSEARCH_TESTS_INDEX = "mojptests"


MOCK_DATA_FOR_SYNC = [
    {"source": CLEARMASH_SOURCE_ID, "id": 1, "version": "five", "collection": COLLECTION_PLACES,
     "source_doc": {"title": "foobar", "content": "bazbax", "implemented": "not yet", "sorry": True},
     "title": {"el":"Greek title ελληνικά, elliniká"}, "title_he": "", "title_en": "",
     "content_html": {"el":"greek content<br/><b>HTML!</b>"}, "content_html_en": "foo", "content_html_he": "bar"},
    {"source": CLEARMASH_SOURCE_ID, "id": "2", "version": "five", "collection": COLLECTION_FAMILY_NAMES,
     "source_doc": {"title": "222", "content": "2222", "implemented": "not yet", "sorry": True},
     "title": {}, "title_he": "", "title_en": "",
     "content_html": {"it":"italian content<br/><b>HTML!</b>"}, "content_html_en": "foo", "content_html_he": "bar"}
]

EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC = [{"version": "five",
                                         "source": "clearmash",
                                         "source_id": "1",
                                         "collection": "places",
                                         "title_el": "Greek title ελληνικά, elliniká",
                                         "slug_el": "clearmash_place_greek-title-ελληνικά-elliniká",
                                         "slugs": ["clearmash_place_greek-title-ελληνικά-elliniká"],
                                         "title_el_lc": "greek title ελληνικά, elliniká",
                                         "title_he": "",
                                         "title_he_suggest": "_",
                                         "title_en": "",
                                         "title_en_suggest": "_",
                                         "title_he_lc": "",
                                         "title_en_lc": "",
                                         "content_html_el": "greek content<br/><b>HTML!</b>",
                                         "content_html_en": "foo",
                                         "content_html_he": "bar",
                                         # this is from the source_doc
                                         # (title field was overridden and deleted)
                                         "content": "bazbax",
                                         "implemented": "not yet",
                                         "sorry": "True"},
                                        {"version": "five",
                                         "source": "clearmash",
                                         "source_id": "2",
                                         "collection": "familyNames",
                                         "slug_en": "familyname_2",
                                         "slugs": ["familyname_2"],
                                         "title_he": "",
                                         "title_en": "",
                                         "title_he_suggest": "_",
                                         "title_en_suggest": "_",
                                         "title_he_lc": "",
                                         "title_en_lc": "",
                                         "content_html_it": "italian content<br/><b>HTML!</b>",
                                         "content_html_en": "foo",
                                         "content_html_he": "bar",
                                         "content": "2222",
                                         "implemented": "not yet",
                                         "sorry": "True"}]


def listify_resources(resources):
    return [[row for row in resource] for resource in resources]


def assert_processor(processor_class, mock_settings=None, parameters=None, datapackage=None, resources=None,
                     expected_datapackage=None, expected_resources=None):
    if not mock_settings:
        mock_settings = type("MockSettings", (object,), {})
    if not parameters:
        parameters = {}
    if not datapackage:
        datapackage = {}
    if not resources:
        resources = []
    if not expected_datapackage:
        expected_datapackage = {}
    if not expected_resources:
        expected_resources = []
    datapackage, resources = processor_class(parameters, datapackage, resources, mock_settings).spew()
    assert datapackage == expected_datapackage, "expected={}, actual={}".format(expected_datapackage, datapackage)
    if expected_resources:
        resources = listify_resources(resources)
        assert resources == expected_resources, \
            "expected={}, actual={}".format(expected_resources, resources)
    else:
        return resources

def assert_conforms_to_dbs_schema(row):
    return assert_conforms_to_schema(DBS_DOCS_TABLE_SCHEMA, row)

def assert_conforms_to_schema(schema, doc):
    row = [doc[field["name"]] for field in schema["fields"]]
    try:
        Schema(schema).cast_row(row)
    except Exception as e:
        logging.exception(e)
        raise Exception("row does not conform to schema\nrow='{}'\nschema='{}'".format(json.dumps(row),
                                                                                       json.dumps(schema)))
    schema_model = SchemaModel(schema)
    res = {}
    for k, v in doc.items():
        try:
            res[k] = schema_model.cast(k, v)
        except Exception as e:
            logging.exception(e)
            raise Exception("doc attribute '{}' with value '{}' "
                            "does not conform to schema '{}'".format(*map(json.dumps, [k, v, schema])))
    return res

def given_empty_elasticsearch_instance(host="localhost:9200", index=ELASTICSEARCH_TESTS_INDEX):
    es = Elasticsearch(host)
    try:
        es.indices.delete(index)
    except NotFoundError:
        pass
    return es

def when_running_sync_processor_on_mock_data(mock_data=MOCK_DATA_FOR_SYNC, refresh_elasticsearch=None):
    mock_data = [deepcopy(o) for o in mock_data]
    resource = next(assert_processor(
        CommonSyncProcessor,
        mock_settings=type("MockSettings", (object,), {"MOJP_ELASTICSEARCH_DB": "localhost:9200",
                                                       "MOJP_ELASTICSEARCH_INDEX": ELASTICSEARCH_TESTS_INDEX,
                                                       "MOJP_ELASTICSEARCH_DOCTYPE": "common"}),
        parameters={},
        datapackage={'resources': [{'name': DBS_DOCS_RESOURCE_NAME,
                                    'path': '{}.csv'.format(DBS_DOCS_RESOURCE_NAME),
                                    'schema': DBS_DOCS_TABLE_SCHEMA}]},
        resources=[mock_data],
        expected_datapackage={
            'resources': [{
                'name': DBS_DOCS_SYNC_LOG_RESOURCE_NAME,
                'path': '{}.csv'.format(DBS_DOCS_SYNC_LOG_RESOURCE_NAME),
                'schema': DBS_DOCS_SYNC_LOG_TABLE_SCHAME
            }]
        }
    ))
    def inner_generator():
        for row in resource:
            try:
                Schema(DBS_DOCS_SYNC_LOG_TABLE_SCHAME).cast_row(row)
                for k, v in row.items():
                    SchemaModel(DBS_DOCS_SYNC_LOG_TABLE_SCHAME).cast(k, v)
            except Exception:
                logging.exception("exception while validating dbs sync log schema\n"
                                  "row={}".format(json.dumps(row)))
                raise
            if refresh_elasticsearch:
                # ensure elasticsearch is refreshed after every document
                refresh_elasticsearch.indices.refresh()
            yield row
    return inner_generator()

def es_doc(es, source, source_id):
    return es.get(ELASTICSEARCH_TESTS_INDEX, id="{}_{}".format(source, source_id)).get("_source")

import json
from datapackage_pipelines_mojp.clearmash.processors.download import ClearmashDownloadProcessor
from datapackage_pipelines_mojp.clearmash.processors.convert import ClearmashConvertProcessor
from datapackage_pipelines_mojp.common.processors.sync import DBS_DOCS_TABLE_SCHEMA
from .common import assert_processor, assert_conforms_to_dbs_schema, assert_conforms_to_schema
from datapackage_pipelines_mojp.clearmash.constants import (CLEARMASH_SOURCE_ID, DOWNLOAD_TABLE_SCHEMA)
from datapackage_pipelines_mojp.common.constants import COLLECTION_FAMILY_NAMES


def given_mock_clearmash_downloaded_doc():
    settings = type("MockSettings", (object,), {})
    datapackage, resources = ClearmashDownloadProcessor(parameters={"mock": True},
                                                        datapackage={"resources": []},
                                                        resources=[],
                                                        settings=settings).spew()
    downloaded_doc = next(next(resources))
    return datapackage, downloaded_doc


def given_mock_clearmash_dbs_doc():
    datapackage, downloaded_doc = given_mock_clearmash_downloaded_doc()
    assert_mock_clearmash_downloaded_doc(downloaded_doc)
    resources = assert_processor(ClearmashConvertProcessor,
                                 parameters={}, datapackage=datapackage, resources=[[downloaded_doc]],
                                 expected_datapackage={"resources": [{"name": "dbs_docs",
                                                                      "path": "dbs_docs.csv",
                                                                      "schema": DBS_DOCS_TABLE_SCHEMA}]})
    converted_doc = next(next(resources))
    return converted_doc



def assert_mock_clearmash_downloaded_doc(downloaded_doc):
    assert_conforms_to_schema(DOWNLOAD_TABLE_SCHEMA, downloaded_doc)
    assert list(downloaded_doc.keys()) == ['document_id', 'item_id', 'item_url', 'template_changeset_id',
                                           'template_id', 'metadata', 'parsed_doc', 'changeset', "collection"]
    assert downloaded_doc["document_id"] == "foobarbaz-4501"
    assert downloaded_doc["item_id"] == 4501
    assert downloaded_doc["item_url"] == "http://foo.bar.baz/4501"
    assert downloaded_doc["template_changeset_id"] == 135
    assert downloaded_doc["template_id"] == "fake-template-45"
    assert downloaded_doc["changeset"] == 707207
    assert downloaded_doc["collection"] == COLLECTION_FAMILY_NAMES
    metadata = json.loads(downloaded_doc["metadata"])
    assert list(metadata.keys()) == ['ActiveLock', 'CreatorUserId', 'EntityTypeId', 'IsArchived', 'IsBookmarked',
                                     'IsLiked', 'LikesCount']
    parsed_doc = json.loads(downloaded_doc["parsed_doc"])
    assert list(parsed_doc.keys()) == ['entity_has_pending_changes', 'is_archived', 'is_deleted',
                                       '_c6_beit_hatfutsot_bh_base_template_ugc',
                                       '_c6_beit_hatfutsot_bh_base_template_old_numbers_parent',
                                       '_c6_beit_hatfutsot_bh_base_template_display_status',
                                       '_c6_beit_hatfutsot_bh_base_template_rights',
                                       '_c6_beit_hatfutsot_bh_base_template_working_status',
                                       '_c6_beit_hatfutsot_bh_place_place_type',
                                       'entity_creation_date',
                                       'EntityFirstPublishDate',
                                       'EntityLastPublishDate',
                                       '_c6_beit_hatfutsot_bh_base_template_last_updated_date_bhp',
                                       'community_id',
                                       'entity_id',
                                       'entity_type_id',
                                       'EntityViewsCount',
                                       '_c6_beit_hatfutsot_bh_base_template_description',
                                       '_c6_beit_hatfutsot_bh_base_template_editor_remarks',
                                       'entity_name',
                                       '_c6_beit_hatfutsot_bh_base_template_bhp_unit',
                                       '_c6_beit_hatfutsot_bh_base_template_family_name',
                                       '_c6_beit_hatfutsot_bh_base_template_multimedia_movies',
                                       '_c6_beit_hatfutsot_bh_base_template_multimedia_music',
                                       '_c6_beit_hatfutsot_bh_base_template_multimedia_photos',
                                       '_c6_beit_hatfutsot_bh_base_template_related_exhibition',
                                       '_c6_beit_hatfutsot_bh_base_template_related_musictext',
                                       '_c6_beit_hatfutsot_bh_base_template_related_personality',
                                       '_c6_beit_hatfutsot_bh_base_template_related_place',
                                       '_c6_beit_hatfutsot_bh_base_template_related_recieve_unit',
                                       '_c6_beit_hatfutsot_bh_base_template_source',
                                       '_c6_beit_hatfutsot_bh_place_located_in',
                                       '_c6_beit_hatfutsot_bh_place_locations',
                                       '_c6_beit_hatfutsot_bh_place_personality_birth',
                                       '_c6_beit_hatfutsot_bh_place_personality_death']


def test_download():
    datapackage, doc = given_mock_clearmash_downloaded_doc()
    assert_mock_clearmash_downloaded_doc(doc)

def test_convert_to_dbs_documents():
    doc = given_mock_clearmash_dbs_doc()
    # these are all the attributes available on the dbs doc, received from the clearmash source
    assert list(doc.keys()) == ['source', 'id', 'source_doc', 'version',
                                 "collection", 'title','title_he', 'title_en',
                                 'content_html', 'content_html_he', 'content_html_en']
    # the source and id are the unique identified of the doc within the Mojp dbs
    assert doc["source"] == CLEARMASH_SOURCE_ID
    assert doc["id"] == "4501"
    # source_doc contains a json dump of all the source document metadata and data
    source_doc = json.loads(doc["source_doc"])
    # these are all the attributes available on the source document
    assert list(source_doc.keys()) == ['document_id', 'item_id', 'item_url', 'template_changeset_id',
                                       'template_id', 'metadata', 'parsed_doc', 'changeset', "collection"]
    # make sure the doc really conforms to the common dbs schema
    # this does a strict check which ensures we always have everything we need in every document
    assert_conforms_to_dbs_schema(doc)
    # check some values which we know are in the mock document (and will always be in the mock document)
    # version is based on some values from the source doc - it is how we detect changes in documents for the sync process
    assert doc["version"] == "707207-foobarbaz-4501"
    assert doc["title_en"] == "Neuchatel"
    assert doc["title_he"] == "נשאטל"
    # document content is available only in html
    # TODO: what will we have in case of missing languages? or additional languages?
    assert doc["content_html_en"] == "Neuchatel<br/><br/>German: Neuenburg<br/><br/>The capital of the Neuchatel Canton, Switzerland<br/><br/>In the year 2000 there were 266 Jews living in Neuchatel.<br/><br/>HISTORY<br/><br/>The earliest records of Jews in the canton date to 1288, when a blood libel accusation was levied against the community and a number of Jews were consequently killed. Later, during the Black Death epidemic of 1348-1349 the Jews of Neuchatel were once again the victims of violence when they were blamed for causing the plague. <br/><br/>After 1476 there are no further references to Jews living in the canton until 1767, when a few Jewish people who had arrived from Alsace were expelled. After a subsequent expulsion in 1790, it was only in 1812 that Jews began to return to Neuchatel; they received the right to legally reside in the city in 1830. <br/><br/>The Jewish population of the canton was 144 in 1844. The Jewish population rose to 1,020 in 1900, a result of the community's economic success. Shortly thereafter, however, the community began to decline, and by 1969 there were about 200 Jews living in the city."
    assert doc["content_html_he"] == "\u05e0\u05e9\u05d0\u05d8\u05dc<br/><br/>\u05e2\u05d9\u05e8 \u05d1\u05de\u05e2\u05e8\u05d1 \u05e9\u05d5\u05d5\u05d9\u05d9\u05e5.<br/><br/><br/>\u05d1-1288 \u05e0\u05d4\u05e8\u05d2\u05d5 \u05d9\u05d4\u05d5\u05d3\u05d9\u05dd \u05d1\u05e7\u05d0\u05e0\u05d8\u05d5\u05df \u05d1\u05e9\u05dc \u05e2\u05dc\u05d9\u05dc\u05ea-\u05d3\u05dd, \u05d5\u05d1\u05e2\u05ea \u05e4\u05e8\u05e2\u05d5\u05ea \"\u05d4\u05de\u05d2\u05e4\u05d4 \u05d4\u05e9\u05d7\u05d5\u05e8\u05d4\" (1348) \u05d4\u05d5\u05e2\u05dc\u05d5 \u05d9\u05d4\u05d5\u05d3\u05d9 \u05d4\u05de\u05e7\u05d5\u05dd \u05e2\u05dc \u05d4\u05de\u05d5\u05e7\u05d3.<br/><br/>\u05e0\u05e1\u05d9\u05d5\u05e0\u05d5\u05ea \u05e9\u05dc \u05d9\u05d4\u05d5\u05d3\u05d9\u05dd \u05dc\u05d4\u05ea\u05d9\u05d9\u05e9\u05d1 \u05d1\u05e0\u05e9\u05d0\u05d8\u05dc \u05d1\u05de\u05d0\u05d4 \u05d4-18 \u05e0\u05db\u05e9\u05dc\u05d5. \u05d1-1790 \u05d2\u05d5\u05e8\u05e9\u05d5 \u05de\u05df \u05d4\u05e7\u05d0\u05e0\u05d8\u05d5\u05df \u05d2\u05dd \u05d9\u05d4\u05d5\u05d3\u05d9\u05dd \u05e9\u05e0\u05d7\u05e9\u05d1\u05d5 \u05de\u05d5\u05e2\u05d9\u05dc\u05d9\u05dd \u05dc\u05d9\u05e6\u05d5\u05d0 \u05e9\u05e2\u05d5\u05e0\u05d9\u05dd.<br/><br/>\u05d4\u05ea\u05d9\u05d9\u05e9\u05d1\u05d5\u05ea \u05d7\u05d3\u05e9\u05d4 \u05e9\u05dc \u05d9\u05d4\u05d5\u05d3\u05d9\u05dd \u05d4\u05ea\u05d7\u05d9\u05dc\u05d4 \u05d1- 1812, \u05d5\u05d6\u05db\u05d5\u05ea-\u05d4\u05d9\u05e9\u05d9\u05d1\u05d4 \u05d1\u05e7\u05d0\u05e0\u05d8\u05d5\u05df \u05d4\u05d5\u05e9\u05d2\u05d4 \u05d1-1830.<br/><br/>\u05d1\u05d0\u05de\u05e6\u05e2 \u05d4\u05de\u05d0\u05d4 \u05d4- 19 \u05de\u05e0\u05ea\u05d4 \u05d4\u05e7\u05d4\u05d9\u05dc\u05d4 \u05d4\u05d9\u05d4\u05d5\u05d3\u05d9\u05ea \u05d1\u05e0\u05e9\u05d0\u05d8\u05dc \u05e4\u05d7\u05d5\u05ea \u05de-150 \u05d0\u05d9\u05e9, \u05d5\u05e2\u05dd \u05e9\u05d9\u05e4\u05d5\u05e8 \u05d4\u05de\u05e6\u05d1 \u05d4\u05db\u05dc\u05db\u05dc\u05d9 \u05e2\u05dc\u05d4 \u05de\u05e1\u05e4\u05e8 \u05d4\u05d9\u05d4\u05d5\u05d3\u05d9\u05dd \u05d1\u05e7\u05d0\u05e0\u05d8\u05d5\u05df \u05dc-1,020 \u05d1\u05e1\u05d5\u05e3 \u05d4\u05de\u05d0\u05d4. \u05de\u05db\u05d0\u05df \u05d5\u05d0\u05d9\u05dc\u05da \u05d4\u05d9\u05d4 \u05d1\u05e7\u05d5 \u05d9\u05e8\u05d9\u05d3\u05d4.<br/><br/>\u05d1\u05e9\u05e0\u05ea 1969 \u05d4\u05ea\u05d2\u05d5\u05e8\u05e8\u05d5 \u05d1\u05e0\u05e9\u05d0\u05d8\u05dc \u05db\u05de\u05d0\u05ea\u05d9\u05d9\u05dd \u05d9\u05d4\u05d5\u05d3\u05d9\u05dd."
    # there are some predefined collections which each document must belong to, it's just a string of the collection name
    assert doc["collection"] == COLLECTION_FAMILY_NAMES

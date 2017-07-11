from .common import (given_empty_elasticsearch_instance,
                     when_running_sync_processor_on_mock_data,
                     es_doc,
                     MOCK_DATA_FOR_SYNC,
                     EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC)
from copy import deepcopy
from .mocks.data import FAMILY_NAMES_BEN_AMARA

def assert_item_missing_content(content_html_en, content_html_he, is_synced):
    es = given_empty_elasticsearch_instance()
    item = deepcopy(FAMILY_NAMES_BEN_AMARA)
    if content_html_en == "del":
        del item["content_html_en"]
    else:
        item["content_html_en"] = content_html_en
    if content_html_he == "del":
        del item["content_html_he"]
    else:
        item["content_html_he"] = content_html_he
    sync_log = list(when_running_sync_processor_on_mock_data([item], refresh_elasticsearch=es))
    assert len(sync_log) == 1
    if is_synced:
        assert sync_log[0]["sync_msg"] == "added to ES"
    else:
        assert sync_log[0]["sync_msg"] == "not synced (missing content in en and he)"

def test_sync_with_invalid_collection():
    es = given_empty_elasticsearch_instance()
    mock_data = deepcopy(MOCK_DATA_FOR_SYNC)
    for i, row in enumerate(mock_data):
        if "collection" in row:
            del mock_data[i]["collection"]
    sync_log_resource = when_running_sync_processor_on_mock_data(
        mock_data, refresh_elasticsearch=es)
    assert next(sync_log_resource) == {"source": "clearmash", "id": "1", "version": "five",
                                       "collection": "unknown", "sync_msg": "added to ES"}
    assert next(sync_log_resource) == {"source": "clearmash", "id": "2", "version": "five",
                                       "collection": "unknown", "sync_msg": "added to ES"}
    es_docs = (es_doc(es, "clearmash", id) for id in ["1", "2"])
    doc = deepcopy(EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC[0])
    doc.update(collection="unknown",
               slug_el="clearmash_greek-title-ελληνικά-elliniká",
               slugs=['clearmash_greek-title-ελληνικά-elliniká'])
    assert next(es_docs) == doc


def test_initial_sync():
    es = given_empty_elasticsearch_instance()
    sync_log_resource = when_running_sync_processor_on_mock_data(
        refresh_elasticsearch=es)
    assert next(sync_log_resource) == {"source": "clearmash", "id": "1", "version": "five",
                                       "collection": "places", "sync_msg": "added to ES"}
    assert next(sync_log_resource) == {"source": "clearmash", "id": "2", "version": "five",
                                       "collection": "familyNames", "sync_msg": "added to ES"}
    es_docs = (es_doc(es, "clearmash", id) for id in ["1", "2"])
    assert next(es_docs) == EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC[0]
    assert next(es_docs) == EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC[1]


def test_update():
    # shotrcut functions to get mock data we use later
    mock_data = lambda **kwargs: [dict(MOCK_DATA_FOR_SYNC[0],
                                       id="666", **kwargs)]
    expected_es_doc = lambda **kwargs: dict(
        EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC[0], source_id="666", **kwargs)
    sync_log = lambda **kwargs: dict({"source": "clearmash",
                                      "id": "666", "collection": "places"}, **kwargs)
    # do initial sync for a specific doc to ES
    es = given_empty_elasticsearch_instance()
    sync_log_resource = when_running_sync_processor_on_mock_data(mock_data(version="one",
                                                                           title_en="Doc_title"),
                                                                 refresh_elasticsearch=es)
    assert next(sync_log_resource) == sync_log(version="one", sync_msg="added to ES")
    assert es_doc(es, "clearmash", "666") == expected_es_doc(version="one",
                                                             title_en="Doc_title",
                                                             title_en_suggest="Doc_title",
                                                             title_en_lc="doc_title",
                                                             slug_en="place_doc-title",
                                                             slug_el="clearmash_place_greek-title-ελληνικά-elliniká",
                                                             slugs=["clearmash_place_greek-title-ελληνικά-elliniká", "place_doc-title"])
    # now, update the item in the mock data, but don't change the version
    sync_log_resource = when_running_sync_processor_on_mock_data(mock_data(version="one",
                                                                           title_en="new_doc_title"),
                                                                 refresh_elasticsearch=es)
    # no update - because we rely on version to determine if to update or not
    assert next(sync_log_resource) == sync_log(
        version="one", sync_msg="no update needed")
    # now, update with a change in version
    sync_log_resource = when_running_sync_processor_on_mock_data(mock_data(version="two",
                                                                           title_en="Doc_title",
                                                                           title_he="בדיקה ABC",
                                                                           title={"el": "ElElEl", "es": "FOOBAR"}),
                                                                 refresh_elasticsearch=es)
    assert next(sync_log_resource) == sync_log(version="two", 
                                        sync_msg='updated doc in ES (old version = "one")')
    assert es_doc(es, "clearmash", "666") == expected_es_doc(version="two",
                                                             title_en="Doc_title",
                                                             title_en_suggest="Doc_title",
                                                             slug_en="place_doc-title",
                                                             title_en_lc="doc_title",
                                                             title_he="בדיקה ABC",
                                                             title_he_suggest="בדיקה ABC",
                                                             slug_he="מקום_בדיקה-abc",
                                                             title_he_lc="בדיקה abc",
                                                             title_el="ElElEl",
                                                             slug_el=["clearmash_place_elelel", "clearmash_place_greek-title-ελληνικά-elliniká"],
                                                             title_es="FOOBAR",
                                                             slug_es="clearmash_place_foobar",
                                                             title_el_lc="elelel",
                                                             title_es_lc="foobar",
                                                             slugs=['clearmash_place_elelel', 'place_doc-title',
                                                                    'מקום_בדיקה-abc', 'clearmash_place_foobar',
                                                                    'clearmash_place_greek-title-ελληνικά-elliniká'])
    sync_log_resource = when_running_sync_processor_on_mock_data(mock_data(version="three",
                                                                           title_en="new_doc_title"),
                                                                 refresh_elasticsearch=es)
    # item is updated in ES
    assert next(sync_log_resource) == sync_log(version="three",
                                            sync_msg='updated doc in ES (old version = "two")')


def test_doc_sync_to_es_with_real_clearmash_docs():
    es = given_empty_elasticsearch_instance()
    sync_log = list(when_running_sync_processor_on_mock_data([FAMILY_NAMES_BEN_AMARA], refresh_elasticsearch=es))
    assert len(sync_log) == 1
    assert sync_log[0]["sync_msg"] == "added to ES"


def test_slugs():
    es = given_empty_elasticsearch_instance()
    sync_log = list(when_running_sync_processor_on_mock_data([FAMILY_NAMES_BEN_AMARA], refresh_elasticsearch=es))
    assert len(sync_log) == 1
    assert sync_log[0]["sync_msg"] ==  "added to ES"
    doc = es_doc(es, "clearmash", "115306")
    assert doc["slug_he"] == u"שםמשפחה_\u05d1\u05df-\u05e2\u05de\u05e8\u05d4"
    assert doc["slug_en"] == u"familyname_ben-amara"
    updated_doc = deepcopy(FAMILY_NAMES_BEN_AMARA)
    del updated_doc["title_en"]
    del updated_doc["title_he"]
    updated_doc["version"] = "test_slugs_2"
    sync_log = list(when_running_sync_processor_on_mock_data([updated_doc], refresh_elasticsearch=es))
    assert len(sync_log) == 1
    assert sync_log[0]["sync_msg"] == 'updated doc in ES (old version = "2991606-f91ea044052746a2903d6ee60d9b374b")'
    doc = es_doc(es, "clearmash", "115306")
    slugs = [(k,v) for k,v in doc.items() if k.startswith("slug_")]
    assert slugs == [('slug_en', ['familyname_115306', 'familyname_ben-amara']),
                     ('slug_he', 'שםמשפחה_בן-עמרה')]

def test_item_without_content_should_not_be_synced():
    assert_item_missing_content(content_html_en="del", content_html_he="del", is_synced=False)
    assert_item_missing_content(content_html_en="a", content_html_he="del", is_synced=True)
    assert_item_missing_content(content_html_en="", content_html_he="", is_synced=False)
    assert_item_missing_content(content_html_en="a", content_html_he="", is_synced=True)
    assert_item_missing_content(content_html_en=None, content_html_he=None, is_synced=False)
    assert_item_missing_content(content_html_en="a", content_html_he=None, is_synced=True)

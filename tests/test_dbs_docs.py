from .common import (given_empty_elasticsearch_instance,
                     when_running_sync_processor_on_mock_data,
                     es_doc,
                     MOCK_DATA_FOR_SYNC,
                     EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC)
from copy import deepcopy


def test_sync_with_invalid_collection():
    es = given_empty_elasticsearch_instance()
    mock_data = deepcopy(MOCK_DATA_FOR_SYNC)
    for i, row in enumerate(mock_data):
        if "collection" in row:
            del mock_data[i]["collection"]
    sync_log_resource = when_running_sync_processor_on_mock_data(mock_data, refresh_elasticsearch=es)
    assert next(sync_log_resource) == {"source": "clearmash", "id": "1", "version": "five",
                                       "collection": "unknown", "sync_msg": "added to ES"}
    assert next(sync_log_resource) == {"source": "clearmash", "id": "2", "version": "five",
                                       "collection": "unknown","sync_msg": "added to ES"}
    es_docs = (es_doc(es, "clearmash", id) for id in ["1", "2"])
    doc = deepcopy(EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC[0])
    doc.update(collection="unknown")
    assert next(es_docs) == doc

def test_initial_sync():
    es = given_empty_elasticsearch_instance()
    sync_log_resource = when_running_sync_processor_on_mock_data(refresh_elasticsearch=es)
    assert next(sync_log_resource) == {"source": "clearmash", "id": "1", "version": "five",
                                       "collection": "places", "sync_msg": "added to ES"}
    assert next(sync_log_resource) == {"source": "clearmash", "id": "2", "version": "five",
                                       "collection": "familyNames", "sync_msg": "added to ES"}
    es_docs = (es_doc(es, "clearmash", id) for id in ["1", "2"])
    assert next(es_docs) == EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC[0]
    assert next(es_docs) == EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC[1]

def test_update():
    # shotrcut functions to get mock data we use later
    mock_data = lambda **kwargs: [dict(MOCK_DATA_FOR_SYNC[0], id=666, **kwargs)]
    expected_es_doc = lambda **kwargs: dict(EXPECTED_ES_DOCS_FROM_MOCK_DATA_SYNC[0], source_id="666", **kwargs)
    sync_log = lambda **kwargs: dict({"source": "clearmash", "id": "666", "collection": "places"}, **kwargs)
    # do initial sync for a specific doc to ES
    es = given_empty_elasticsearch_instance()
    sync_log_resource = when_running_sync_processor_on_mock_data(mock_data(version="one", title_en="doc_title"),
                                                                 refresh_elasticsearch=es)
    assert next(sync_log_resource) == sync_log(version="one", sync_msg="added to ES")
    assert es_doc(es, "clearmash", "666") == expected_es_doc(version="one", title_en="doc_title")
    # now, update the item in the mock data, but don't change the version
    sync_log_resource = when_running_sync_processor_on_mock_data(mock_data(version="one", title_en="new_doc_title"),
                                                                 refresh_elasticsearch=es)
    # no update - because we rely on version to determine if to update or not
    assert next(sync_log_resource) == sync_log(version="one", sync_msg="no update needed")
    # now, update with a change in version
    sync_log_resource = when_running_sync_processor_on_mock_data(mock_data(version="two", title_en="new_doc_title"),
                                                                 refresh_elasticsearch=es)
    # item is updated in ES
    assert next(sync_log_resource) == sync_log(version="two", sync_msg='updated doc in ES (old version = "one")')

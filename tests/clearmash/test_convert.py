from datapackage_pipelines_mojp.clearmash.processors.convert import Processor
from .mock_clearmash_api import MockClearmashApi
from ..common import get_mock_settings, assert_processor, assert_dict
from .test_download import get_downloaded_docs


class MockProcessor(Processor):

    def _get_clearmash_api(self):
        return MockClearmashApi()

def get_clearmash_convert_resource_data(downloaded_docs=None):
    if not downloaded_docs:
        downloaded_docs = get_downloaded_docs()
        expected_len = 5
    else:
        expected_len = None
    processor = MockProcessor(parameters={"input-resource": "entities", "output-resource": "dbs-docs"},
                              datapackage={"resources": [{"name": "entities"}]},
                              resources=[downloaded_docs],
                              settings=get_mock_settings())
    docs = assert_processor(processor)
    if expected_len:
        assert len(docs) == expected_len
    return docs


def test_clearmash_convert():
    resource = get_clearmash_convert_resource_data()
    assert len(resource) == 5
    assert len(resource[0].pop("content_html_he")) == 1060
    assert len(resource[0].pop("content_html_en")) == 1399
    assert_dict(resource[0], {"collection": "familyNames",
                              "content_html": {},
                              "title_en": "BEN AMARA",
                              "title_he": "בן עמרה",
                              "title": {},
                              "id": "115306",
                              "source": "clearmash",
                              "version": "6468918-f91ea044052746a2903d6ee60d9b374b",
                              "related_documents": {},
                              "main_image_url": "",
                              "main_thumbnail_image_url": "",
                              "keys": ['source_doc']})
    assert_dict(resource[1], {"collection": "places"})
    assert_dict(resource[2], {"collection": "movies"})
    assert_dict(resource[3], {"collection": "personalities"})
    assert_dict(resource[4],
                {"collection": "photoUnits", "id": "115301",
                 "main_image_url": "https://bhfiles.clearmash.com/MediaServer/Images/5ff94861dad3480c9e59f1904a825caf_1024x1024.JPG",
                 "main_thumbnail_image_url": "https://bhfiles.clearmash.com/MediaServer/Images/5ff94861dad3480c9e59f1904a825caf_260x260.JPG"})

def test_clearmash_convert_photoUnits():
    entity_ids = [{"item_id": 203884, "collection": "photoUnits"},]
    resource = get_clearmash_convert_resource_data(get_downloaded_docs(entity_ids))
    assert len(resource) == 1
    assert_dict(resource[0], {'main_image_url': 'https://bhfiles.clearmash.com/MediaServer/Images/fff406c76ce942f9a37a19dcc061a36b_1024x1024.JPG',
                              'main_thumbnail_image_url': 'https://bhfiles.clearmash.com/MediaServer/Images/fff406c76ce942f9a37a19dcc061a36b_260x260.JPG'})

def test_clearmash_should_skip_entity_with_pending_changes():
    # these entities are duplicates of other published entities
    # see #75
    entity_ids = [{"item_id": 200292, "collection": "photoUnits"}]
    downloaded_docs = get_downloaded_docs(entity_ids)
    # entity has pending changes
    assert downloaded_docs[0]["parsed_doc"].get("entity_has_pending_changes") == True
    resource = get_clearmash_convert_resource_data(get_downloaded_docs(entity_ids))
    # skipped by convert processor
    assert len(resource) == 0


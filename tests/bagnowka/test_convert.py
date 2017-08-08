# /mojp-dbs-pipelines/tests/bagnowka/test_convert.py
from datapackage_pipelines.wrapper import spew
from datapackage_pipelines_mojp.bagnowka.processors.download import BagnowkaDownloadProcessor
from datapackage_pipelines_mojp.bagnowka.processors.convert import BagnowkaConvertProcessor
from ..common import assert_conforms_to_schema, get_mock_settings, assert_processor, assert_dict
from .test_download import MockBagnowkaDownloadProcessor, test_bagnowka_download
import os
import json


def get_bagnowka_convert_resource_data():
    d_parameters = {"add-resource": "bagnowka"}
    d_datapackage = {"resources": []}
    d_resources = []
    processor = BagnowkaConvertProcessor(parameters={"input-resource": "bagnowka", "output-resource": "dbs-docs"},
                              datapackage={"resources": [
                                  {"name": "bagnowka"}]},
                              resources=[MockBagnowkaDownloadProcessor(
                                  d_parameters, d_datapackage, d_resources)._get_resource()],
                              settings=get_mock_settings())
    docs = assert_processor(processor)
    assert len(docs) == 10
    return docs


def test_converted_docs():
    docs = get_bagnowka_convert_resource_data()
    assert len(docs) == 10
    assert_dict(docs[0], {'collection': 'photoUnits', 'content_html': {}, 'title_en': 'Tuchola, 1910', 'title_he': '', 'title': {}, 'id': '11111111112901', 'source': 'Bagnowka', 'version': 'one', 'related_documents': {}, 'main_image_url': 'https://s3-us-west-2.amazonaws.com/bagnowka-scraped/full/6b4cbf325dc30b5046c1e4b458c2e712f2a05ef6.jpg', 'main_thumbnail_image_url': 'https://s3-us-west-2.amazonaws.com/bagnowka-scraped/thumbs/small/6b4cbf325dc30b5046c1e4b458c2e712f2a05ef6.jpg'})
    assert docs[1]["id"] == "11111111117135"
    assert docs[5]["title_en"] == "Grajewo - the people, soldiers, 1916"

def assert_processor(processor):
    datapackage, resources, stats = processor.spew()
    resources = list(resources)
    assert len(resources) == 1
    resource = list(resources[0])
    for doc in resource:
        assert_conforms_to_schema(datapackage["resources"][0]["schema"], doc)
    return resource

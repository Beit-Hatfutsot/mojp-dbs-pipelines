from .common import assert_processor
from mojp_dbs_pipelines.wikipedia.processors.download import WikipediaDownloadProcessor
# from mojp_dbs_pipelines.wikipedia.processors.convert import WikipediaConvertProcessor
import json, os
from urllib.parse import urlparse, parse_qs


class MockWikipediaDownloadProcessor(WikipediaDownloadProcessor):

    def _get_title_json(self, url):
        scheme, netloc, path, params, query, fragment = urlparse(url)
        if path == "/w/api.php":
            lang = "he" if netloc == "he.wikipedia.org" else "en"
            qs = parse_qs(query)
            page = qs["page"][0]
            filename = "{}-{}.json".format(lang, page)
            full_filename = os.path.join(os.path.dirname(__file__), "wikipedia-mocks", filename)
            if os.environ.get("WIKIPEDIA_WRITE_MOCKS") == "1":
                data = super(MockWikipediaDownloadProcessor, self)._get_title_json(url)
                with open(full_filename, "w") as f:
                    json.dump(data, f)
            else:
                with open(full_filename) as f:
                    data = json.load(f)
            return data
        else:
            raise Exception("invalud url: {}".format(url))

def test_download():
    assert_processor(
        MockWikipediaDownloadProcessor,
        parameters={},
        datapackage={"resources": []},
        resources=[],
        expected_datapackage={
            "resources": [{
                "name": "wikipedia",
                "path": "wikipedia.csv",
                "schema": {"fields": [
                    {"name": "id", "type": "integer"},
                    {"name": "source_doc", "type": "string"}
                ]}
            }]
        },
        expected_resources=[[
            {"id": 1, "source_doc": json.dumps({"title": "foobar", "content": "bazbax"})},
            {"id": 2, "source_doc": json.dumps({"title": "222", "content": "2222"})}
        ]]
    )


# def test_convert_to_dbs_documents():
#     assert_processor(
#         ClearmashConvertProcessor,
#         parameters={},
#         datapackage={
#             "resources": [{
#                 "name": "clearmash",
#                 "path": "clearmash.csv",
#                 "schema": {"fields": [
#                     {"name": "id", "type": "integer"},
#                     {"name": "source_doc", "type": "string"}
#                 ]}
#             }]
#         },
#         resources=[[
#             {"id": 1, "source_doc": json.dumps({"title": "foobar", "content": "bazbax"})},
#             {"id": 2, "source_doc": json.dumps({"title": "222", "content": "2222"})}
#         ]],
#         expected_datapackage={
#             "resources": [{
#                 "name": "dbs_docs",
#                 "path": "dbs_docs.csv",
#                 "schema": {"fields": [
#                     {"name": "source", "type": "string"},
#                     {"name": "id", "type": "string"},
#                     {'name': 'version', 'type': 'string', 'description': 'source dependant field, used by sync process to detect document updates'},
#                     {"name": "source_doc", "type": "string"}
#                 ]}
#             }]
#         },
#         expected_resources=[[
#             {"source": "clearmash", "id": "1", "version": "5",
#              "source_doc": '{"title": "foobar", "content": "bazbax", "implemented": "not yet", "sorry": true}'},
#             {"source": "clearmash", "id": "2", "version": "5",
#              "source_doc": '{"title": "222", "content": "2222", "implemented": "not yet", "sorry": true}'}
#         ]]
#     )

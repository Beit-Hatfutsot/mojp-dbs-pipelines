from datapackage_pipelines_mojp.clearmash.api import (ClearmashApi,
                                                      parse_error_response_content,
                                                      parse_clearmash_document,
                                                      parse_clearmash_documents,
                                                      ClearmashRelatedDocuments,
                                                      ClearmashChildDocuments,
                                                      ClearmashMediaGalleries,
                                                      ClearmashStartDate)
import os, json
from requests.exceptions import HTTPError
from datapackage_pipelines_mojp.clearmash.constants import WEB_CONTENT_FOLDER_ID_Place


class MockClearmashApi(ClearmashApi):

    def mock_invalid_call(self):
        return self._wcm_api_call("/invalid/path")

    def _get_mock_url_request_json(self, filename, callback):
        if not os.path.exists(filename):
            res = callback()
            with open(filename, "w") as f:
                json.dump(res, f, indent=4)
        with open(filename) as f:
            return json.load(f)

    def _get_request_json(self, url, headers, post_data=None):
        if url == "https://bh.clearmash.com/API/V5/Services/WebContentManagement.svc/CommunityPage/Folder/Root":
            filename = os.path.join(os.path.dirname(__file__), "mocks", "clearmash-api-communitypage-folder-root.json")
        elif url == "https://bh.clearmash.com/API/V5/Services/WebContentManagement.svc/invalid/path":
            filename = os.path.join(os.path.dirname(__file__), "mocks", "clearmash-api-invalid-path-response.json")
        elif url == "https://bh.clearmash.com/API/V5/Services/WebContentManagement.svc/Document/Folder/Root":
            filename = os.path.join(os.path.dirname(__file__), "mocks", "clearmash-api-document-folder-root.json")
        elif url == "https://bh.clearmash.com/API/V5/Services/WebContentManagement.svc/Document/Folder/Get":
            filename = os.path.join(os.path.dirname(__file__), "mocks",
                                    "clearmash-api-document-folder-get-{}.json".format(post_data["FolderId"]))
        elif url == "https://bh.clearmash.com/API/V5/Services/WebContentManagement.svc/Documents/Get":
            filename = os.path.join(os.path.dirname(__file__), "mocks",
                                    "clearmash-api-documents-get-{}.json".format("-".join(map(str, post_data["entitiesIds"]))))
        elif url == "https://bh.clearmash.com/API/V5/Services/WebContentManagement.svc/Document/ByRelationField":
            filename = os.path.join(os.path.dirname(__file__), "mocks", "clearmash-api-get-related-docs-by-item-field-{}-{}-{}.json".format(post_data["EntityId"], post_data["FieldId"], post_data["MaxNestingDepth"]))
        else:
            filename = None
        if filename:
            def get_res():
                try:
                    return super(MockClearmashApi, self)._get_request_json(url, headers, post_data)
                except HTTPError as e:
                    return {"__MOJP_ERROR__": True,
                            "status_code": e.response.status_code,
                            "content": e.response.content.decode()}
            res = self._get_mock_url_request_json(filename, get_res)
            if isinstance(res, dict) and res.pop("__MOJP_ERROR__", False):
                raise HTTPError(response=type("MockResponse", (object,), res))
            else:
                return res
        else:
            raise Exception("invalid url: {}".format(url))

class MockClearmashRelatedDocuments(ClearmashRelatedDocuments):

    def get_clearmash_api(self):
        return MockClearmashApi()

class MockClearmashChildDocuments(ClearmashChildDocuments):

    def get_clearmash_api(self):
        return MockClearmashApi()

class MockClearmashMediaGalleries(ClearmashMediaGalleries):

    def get_clearmash_api(self):
        return MockClearmashApi()

def test_invalid_call():
    try:
        MockClearmashApi().mock_invalid_call()
        assert False
    except HTTPError as e:
        assert e.response.status_code == 400
        assert parse_error_response_content(e.response.content) == [
            'Request Error',
            "The server encountered an error processing the request. "
            "The exception message is 'Value cannot be null.\r\n"
            "Parameter name: operationMethod'. "
            "See server logs for more details. "
            "The exception stack trace is: ",
            '   at ClearMash.ServerAPI.Common.Security.RequestHeaders.BasicHeaders..ctor(MethodInfo operationMethod, String clientToken)\r\n'
            '   at ClearMash.ServerAPI.Common.Security.RequestHeaders.Create(Type serviceType, String operationName, String clientToken, String personToken, String systemToken)\r\n'
            '   at ClearMash.ServerAPI.Common.Security.ClientValidationMessageInspectorREST.GetRequestHeaders(OperationContext operationContext, Message request)\r\n'
            '   at ClearMash.ServerAPI.Common.Security.ClientValidationMessageInspector.AfterReceiveRequest(Message& request, IClientChannel channel, InstanceContext instanceContext)\r\n'
            '   at System.ServiceModel.Dispatcher.ImmutableDispatchRuntime.AfterReceiveRequestCore(MessageRpc& rpc)\r\n'
            '   at System.ServiceModel.Dispatcher.ImmutableDispatchRuntime.ProcessMessage2(MessageRpc& rpc)\r\n'
            '   at System.ServiceModel.Dispatcher.ImmutableDispatchRuntime.ProcessMessage11(MessageRpc& rpc)\r\n'
            '   at System.ServiceModel.Dispatcher.MessageRpc.Process(Boolean isOperationContextSet)'
        ]

def test_get_root_folder():
    true, false = True, False  # json compatibility
    bh_root_folder = MockClearmashApi().get_bh_root_folder()
    assert bh_root_folder["Name"] == "בית התפוצות"
    assert bh_root_folder["CommunityId"] == 6
    assert bh_root_folder["Id"] == 6

def test_get_documents_root_folders():
    root_folders = MockClearmashApi().get_documents_root_folders()
    assert {folder["Id"]: folder["Name"] for folder in root_folders} == {40: 'סרטים',
                                                                         41: 'מוסיקה',
                                                                         42: 'תמונות',
                                                                         43: 'מקום',
                                                                         44: 'משפחה',
                                                                         45: 'שם משפחה',
                                                                         46: 'תערוכה',
                                                                         47: 'מוסיקה טקסט',
                                                                         48: 'יחידת קבלה',
                                                                         49: 'אישיות',
                                                                         50: 'ערך',
                                                                         51: 'עץ משפחה',
                                                                         53: 'מקור'}

def test_get_web_document_system_folder_places():
    document_folder = MockClearmashApi().get_web_document_system_folder(WEB_CONTENT_FOLDER_ID_Place)
    folders = document_folder.pop("Folders")
    items = document_folder.pop("Items")
    assert len(document_folder) == 0
    assert len(folders) == 0
    assert len(items) == 6541
    item = items[6240]
    assert item["Id"] == 258770
    assert item["Name"] == "מזוצ'אט"
    assert {item["Id"]: item["Name"] for item in items[:5]} == {115325: 'נשאטל',
                                                                115353: 'קנטרברי',
                                                                115365: "קצ'קמט",
                                                                115371: "יז'יורי",
                                                                115388: 'הלובוקה נאד ולטאבואו'}

def test_get_documents_places():
    documents_response = MockClearmashApi().get_documents([115325, 115353, 115365, 115371, 115388, 265694])
    reference_datasource_items = documents_response.pop("ReferencedDatasourceItems")
    entities = documents_response.pop("Entities")
    assert len(documents_response) == 0
    assert len(entities) == 6
    assert len(reference_datasource_items) == 6
    first_entity = entities[0]
    assert first_entity.pop("Acl") == None
    assert first_entity.pop("Changeset") == 6219337
    document = first_entity.pop("Document")
    template_reference = document.pop("TemplateReference")
    assert template_reference.pop("ChangesetId") == 5135675  # the template changeset id
    assert template_reference.pop("TemplateId") == "_c6_beit_hatfutsot_bh_place"
    assert len(template_reference) == 0
    metadata = first_entity.pop("Metadata")
    assert list(metadata.keys()) == ['ActiveLock', 'CreatorUserId', 'EntityTypeId', 'Id',
                                     'IsArchived', 'IsBookmarked', 'IsLiked', 'LikesCount', 'Url']
    assert metadata["Id"] == 115325  # same as the requested document id
    assert metadata["Url"] == "http://bh.clearmash.com/skn/c6/dummy/e115325/dummy/"  # url in clearmash
    assert len(first_entity) == 0
    assert document.pop("Id") == "65e99e43a7164999971d8336a53f335e"
    parsed_doc = parse_clearmash_document(document, reference_datasource_items)
    assert len(parsed_doc) == 37
    assert parsed_doc["entity_has_pending_changes"] == False
    assert parsed_doc["is_archived"] == False
    assert parsed_doc["is_deleted"] == False
    assert parsed_doc["entity_name"] == {"en": "Neuchatel", "he": "\u05e0\u05e9\u05d0\u05d8\u05dc"}
    assert parsed_doc["_c6_beit_hatfutsot_bh_base_template_bhp_unit"] == {"en": "72182"}
    assert parsed_doc["_c6_beit_hatfutsot_bh_base_template_ugc"] == False
    assert parsed_doc["_c6_beit_hatfutsot_bh_base_template_display_status"] == [{'en': 'Museum only', 'he': 'מוזיאון בלבד'}]
    assert parsed_doc["_c6_beit_hatfutsot_bh_base_template_rights"] == [{'en': 'Full', 'he': 'מלא'}]
    assert parsed_doc["_c6_beit_hatfutsot_bh_base_template_working_status"] == [{'en': 'Completed', 'he': 'הסתיים'}]
    assert parsed_doc["_c6_beit_hatfutsot_bh_base_template_description"] == {"en": "Neuchatel<br/><br/>German: Neuenburg<br/><br/>The capital of the Neuchatel Canton, Switzerland<br/><br/>In the year 2000 there were 266 Jews living in Neuchatel.<br/><br/>HISTORY<br/><br/>The earliest records of Jews in the canton date to 1288, when a blood libel accusation was levied against the community and a number of Jews were consequently killed. Later, during the Black Death epidemic of 1348-1349 the Jews of Neuchatel were once again the victims of violence when they were blamed for causing the plague. <br/><br/>After 1476 there are no further references to Jews living in the canton until 1767, when a few Jewish people who had arrived from Alsace were expelled. After a subsequent expulsion in 1790, it was only in 1812 that Jews began to return to Neuchatel; they received the right to legally reside in the city in 1830. <br/><br/>The Jewish population of the canton was 144 in 1844. The Jewish population rose to 1,020 in 1900, a result of the community's economic success. Shortly thereafter, however, the community began to decline, and by 1969 there were about 200 Jews living in the city.", "he": "\u05e0\u05e9\u05d0\u05d8\u05dc<br/><br/>\u05e2\u05d9\u05e8 \u05d1\u05de\u05e2\u05e8\u05d1 \u05e9\u05d5\u05d5\u05d9\u05d9\u05e5.<br/><br/><br/>\u05d1-1288 \u05e0\u05d4\u05e8\u05d2\u05d5 \u05d9\u05d4\u05d5\u05d3\u05d9\u05dd \u05d1\u05e7\u05d0\u05e0\u05d8\u05d5\u05df \u05d1\u05e9\u05dc \u05e2\u05dc\u05d9\u05dc\u05ea-\u05d3\u05dd, \u05d5\u05d1\u05e2\u05ea \u05e4\u05e8\u05e2\u05d5\u05ea \"\u05d4\u05de\u05d2\u05e4\u05d4 \u05d4\u05e9\u05d7\u05d5\u05e8\u05d4\" (1348) \u05d4\u05d5\u05e2\u05dc\u05d5 \u05d9\u05d4\u05d5\u05d3\u05d9 \u05d4\u05de\u05e7\u05d5\u05dd \u05e2\u05dc \u05d4\u05de\u05d5\u05e7\u05d3.<br/><br/>\u05e0\u05e1\u05d9\u05d5\u05e0\u05d5\u05ea \u05e9\u05dc \u05d9\u05d4\u05d5\u05d3\u05d9\u05dd \u05dc\u05d4\u05ea\u05d9\u05d9\u05e9\u05d1 \u05d1\u05e0\u05e9\u05d0\u05d8\u05dc \u05d1\u05de\u05d0\u05d4 \u05d4-18 \u05e0\u05db\u05e9\u05dc\u05d5. \u05d1-1790 \u05d2\u05d5\u05e8\u05e9\u05d5 \u05de\u05df \u05d4\u05e7\u05d0\u05e0\u05d8\u05d5\u05df \u05d2\u05dd \u05d9\u05d4\u05d5\u05d3\u05d9\u05dd \u05e9\u05e0\u05d7\u05e9\u05d1\u05d5 \u05de\u05d5\u05e2\u05d9\u05dc\u05d9\u05dd \u05dc\u05d9\u05e6\u05d5\u05d0 \u05e9\u05e2\u05d5\u05e0\u05d9\u05dd.<br/><br/>\u05d4\u05ea\u05d9\u05d9\u05e9\u05d1\u05d5\u05ea \u05d7\u05d3\u05e9\u05d4 \u05e9\u05dc \u05d9\u05d4\u05d5\u05d3\u05d9\u05dd \u05d4\u05ea\u05d7\u05d9\u05dc\u05d4 \u05d1- 1812, \u05d5\u05d6\u05db\u05d5\u05ea-\u05d4\u05d9\u05e9\u05d9\u05d1\u05d4 \u05d1\u05e7\u05d0\u05e0\u05d8\u05d5\u05df \u05d4\u05d5\u05e9\u05d2\u05d4 \u05d1-1830.<br/><br/>\u05d1\u05d0\u05de\u05e6\u05e2 \u05d4\u05de\u05d0\u05d4 \u05d4- 19 \u05de\u05e0\u05ea\u05d4 \u05d4\u05e7\u05d4\u05d9\u05dc\u05d4 \u05d4\u05d9\u05d4\u05d5\u05d3\u05d9\u05ea \u05d1\u05e0\u05e9\u05d0\u05d8\u05dc \u05e4\u05d7\u05d5\u05ea \u05de-150 \u05d0\u05d9\u05e9, \u05d5\u05e2\u05dd \u05e9\u05d9\u05e4\u05d5\u05e8 \u05d4\u05de\u05e6\u05d1 \u05d4\u05db\u05dc\u05db\u05dc\u05d9 \u05e2\u05dc\u05d4 \u05de\u05e1\u05e4\u05e8 \u05d4\u05d9\u05d4\u05d5\u05d3\u05d9\u05dd \u05d1\u05e7\u05d0\u05e0\u05d8\u05d5\u05df \u05dc-1,020 \u05d1\u05e1\u05d5\u05e3 \u05d4\u05de\u05d0\u05d4. \u05de\u05db\u05d0\u05df \u05d5\u05d0\u05d9\u05dc\u05da \u05d4\u05d9\u05d4 \u05d1\u05e7\u05d5 \u05d9\u05e8\u05d9\u05d3\u05d4.<br/><br/>\u05d1\u05e9\u05e0\u05ea 1969 \u05d4\u05ea\u05d2\u05d5\u05e8\u05e8\u05d5 \u05d1\u05e0\u05e9\u05d0\u05d8\u05dc \u05db\u05de\u05d0\u05ea\u05d9\u05d9\u05dd \u05d9\u05d4\u05d5\u05d3\u05d9\u05dd."}

def test_get_related_docs_of_item():
    related = MockClearmashApi().get_document_related_docs_by_fields(220590, "_c6_beit_hatfutsot_bh_base_template_multimedia_photos")
    photo_id = related["Entities"][0]["Document"]["Fields_Int32"][1]["Value"]
    photo_url = related["Entities"][1]["Document"]["Fields_ChildDocuments"][2]["ChildDocuments"][0]["Value"]["Fields_MediaGalleries"][0]["Galleries"][0]["GalleryItems"][0]["ItemDocument"]["Value"]["Fields_LocalizedText"][1]["Value"][0]["Value"]
    assert photo_id == 123737
    assert photo_url == "~~st~~c72ca946fa684845b566949b38e35506.JPG"

def test_get_related_documents():
    docs = list(parse_clearmash_documents(MockClearmashApi().get_documents([115353])))
    related_docs = MockClearmashRelatedDocuments.get_for_doc(docs[0])
    photos = related_docs["_c6_beit_hatfutsot_bh_base_template_multimedia_photos"]
    assert photos.first_page_results == ['aa7f0fa3c54d44a1b8e59f695f921dd5', '92e5a62105bc4813b61b3e702c0561d6']
    assert photos.total_count == 2
    related_documents = list(photos.get_related_documents())
    assert len(related_documents) == 2
    assert related_documents[0]["document_id"] == "aa7f0fa3c54d44a1b8e59f695f921dd5"
    assert related_documents[0]["parsed_doc"]["entity_name"] == {
        'en': 'Naim Dangoor and the Archbishop of Canterbury, London, England 1988',
        'he': 'נעים דנגור והארכיבישוף מקנטרברי בכנס לענייני דתות, לונדון, אנגליה 1988'}
    assert related_documents[1]["document_id"] == "92e5a62105bc4813b61b3e702c0561d6"

def test_get_child_documents():
    parent_doc = next(parse_clearmash_documents(MockClearmashApi().get_documents([164467])))
    child_docs = MockClearmashChildDocuments.get_for_doc(parent_doc)
    assert len(child_docs) == 5
    films_multimedia_child_docs = child_docs["_c6_beit_hatfutsot_bh_films_multimedia"]
    assert len(films_multimedia_child_docs) == 1
    child_doc = films_multimedia_child_docs[0]
    assert child_doc.document_id == "1cab6a4ff19b4e688c9a406d1ad4fd40"
    assert child_doc.template_reference == {'ChangesetId': 5135675, 'TemplateId': '_c6_beit_hatfutsot_bh_multimedia_film'}
    assert child_doc.parsed_doc["_c6_beit_hatfutsot_bh_multimedia_film_movie_mg"][0] == "MediaGalleries"

def test_get_media_galleries():
    parent_doc = next(parse_clearmash_documents(MockClearmashApi().get_documents([164467])))
    films_multimedia_child_docs = MockClearmashChildDocuments.get_for_doc(parent_doc)["_c6_beit_hatfutsot_bh_films_multimedia"]
    child_doc = films_multimedia_child_docs[0]
    media_galleries = MockClearmashMediaGalleries.get_for_child_doc(child_doc)
    film_movie_media_galleries = media_galleries["_c6_beit_hatfutsot_bh_multimedia_film_movie_mg"]
    assert len(film_movie_media_galleries) == 1
    gallery = film_movie_media_galleries[0]
    assert isinstance(gallery, MockClearmashMediaGalleries)
    assert sorted(gallery.gallery_main_document.keys()) == ["doc", "document_id", "template_reference"]
    assert len(gallery.gallery_items) == 1
    gallery_item = gallery.gallery_items[0]
    assert gallery_item["MediaUrls"] == {'MPEG4': '00000000115f42d69144c7d2bb86466f',
                                         'Ogg': '00000000084b4d59833e5f3b87917cc0',
                                         'WebM': '000000007cd549cbaba47038cc570d2b'}
    assert gallery_item["PosterImageUrl"] == "~~st~~8165e9e84f9946a8bf1f3535eaf172f9.jpg"
    assert gallery_item["__type"] == "MediaGalleryVideoItem:http://www.clearmash.com/api/v5/services.Documents"
    assert sorted(gallery_item["ItemDocument"].keys()) == ["doc", "document_id", "template_reference"]

def test_get_dates():
    fuzzy = {"Fields_FuzzyDate": [{
                                    "Id": "_c6_beit_hatfutsot_bh_photos_photo_period_fid",
                                    "Value": {
                                        "__type": "FuzzyDateTreeExpression:http://www.clearmash.com/api/v5/services.Documents",
                                        "Value": {
                                            "__type": "ImplicitFuzzyDate:http://www.clearmash.com/api/v5/services",
                                            "Edge": 1,
                                            "Offset": 3,
                                            "ReducedAccuracyDate": {
                                                "__type": "DayAccuracyDate:http://www.clearmash.com/api/v5/services",
                                                "DayNumberOfMonth": 24,
                                                "MonthNumberOfYear": 4,
                                                "YearNumber": 1947
                                            },
                                            "Subrange": 1
                                        }
                                    }
                                }]}
    all_fuzz = fuzzy["Fields_FuzzyDate"][0]
    obj = ClearmashStartDate("_c6_beit_hatfutsot_bh_photos_photo_period_fid", all_fuzz)
    assert obj.get_iso_date() == '1947-04-24T00:00:00Z'
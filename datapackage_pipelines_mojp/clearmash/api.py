from .constants import WCM_BASE_URL, FOLDER_TYPE_WebDocumentSystemFolder
from datapackage_pipelines_mojp import settings
import requests
from pyquery import PyQuery as pq
import os, json
from itertools import cycle
from copy import deepcopy
import logging


def parse_error_response_content(content):
    return [p.text for p in pq(content[2:])("#content p")]

def parse_clearmash_documents(documents_response):
    reference_datasource_items = documents_response.pop("ReferencedDatasourceItems")
    entities = documents_response.pop("Entities")
    for entity in entities:
        document = entity.pop("Document")
        metadata = entity.pop("Metadata")
        template_reference = document.pop("TemplateReference")
        document_id = document.pop("Id")
        parsed_doc = parse_clearmash_document(document, reference_datasource_items)
        yield {"document_id": document_id,
               "item_id": int(metadata.pop("Id")),
               "item_url": metadata.pop("Url"),
               "template_changeset_id": template_reference.pop("ChangesetId"),
               "template_id": template_reference.pop("TemplateId"),
               "metadata": metadata,
               "parsed_doc": parsed_doc,
               "changeset": int(entity.pop("Changeset"))}

def parse_clearmash_document(document, reference_datasource_items):
    parsed_doc = {}
    for k in document:
        if k.startswith("Fields_"):
            fields_type = k[7:]
            for field in document[k]:
                value = (fields_type, field)
                if fields_type in ["Boolean", "Int32", "Int64"]:
                    value = field["Value"]
                elif fields_type == "Datasource":
                    value = []
                    for rdi in reference_datasource_items:
                        if rdi["Id"] in field["DatasourceItemsIds"]:
                            value.append({i["ISO6391"]: i["Value"] for i in rdi["Name"]})
                elif fields_type in ["LocalizedHtml", "LocalizedText"]:
                    value = {i["ISO6391"]: i["Value"] for i in field["Value"]}
                parsed_doc[field["Id"]] = value
        else:
            raise Exception("Unknown field: {}".format(k))
    for k in document:
        fields_type = k[7:]
        for field in document[k]:
            value = (fields_type, field)
            if fields_type == "RelatedDocuments":
                entity_id = parsed_doc["entity_id"]
                first_page_of_results = field["FirstPageOfReletedDocumentsIds"]
                value = ClearmashRelatedDocuments(first_page_of_results, entity_id, field["Id"])
                parsed_doc[field["Id"]] = value
    
    return parsed_doc

class ClearmashRelatedDocuments():
    
    def __init__(self, first_page_of_results, entity_id, field_name):
        self.first_page_of_results = first_page_of_results
        self.entity_id = entity_id
        self.field_name = field_name
    
    def first_page_results(self):
        return self.first_page_of_results

    def get_related_documents(self):
        related_documents = ClearmashApi().get_document_related_docs_by_fields(self.entity_id, self.field_name)
        return related_documents
class ClearmashApi(object):

    def __init__(self, token=None):
        if not token:
            token = settings.CLEARMASH_CLIENT_TOKEN
        self._token = token

    def get_bh_root_folder(self):
        root_folder_by_id = None
        root_folder_by_name = None
        for root_folder in self._wcm_api_call("/CommunityPage/Folder/Root"):
            if root_folder["Name"] == "בית התפוצות":
                if root_folder_by_name:
                    raise Exception("found multiple bh root folders by name")
                else:
                    root_folder_by_name = root_folder
            elif root_folder["CommunityId"] == 6:
                if root_folder_by_id:
                    raise Exception("found multiple bh root folders by id")
                else:
                    root_folder_by_id = root_folder
        if root_folder_by_name:
            return root_folder_by_name
        elif root_folder_by_id:
            return root_folder_by_id
        else:
            raise Exception("could not find root folder")

    def get_documents_root_folders(self):
        return self._wcm_api_call("/Document/Folder/Root")

    def get_web_document_system_folder(self, folder_id):
        return self._wcm_api_call("/Document/Folder/Get", {"FolderId": folder_id,
                                                           "FolderType": FOLDER_TYPE_WebDocumentSystemFolder})

    def get_documents(self, entity_ids):
        return self._wcm_api_call("/Documents/Get", {"entitiesIds": entity_ids})

    def get_document_related_docs_by_fields(self, entity_id, field, max_nesting_depth=1):
        return self._wcm_api_call("/Document/ByRelationField", {"EntityId": entity_id, "FieldId": field, "MaxNestingDepth": max_nesting_depth})

    def _wcm_api_call(self, path, post_data=None):
        return self._get_request_json("{}{}".format(WCM_BASE_URL, path),
                                      headers=self._get_headers(),
                                      post_data=post_data)

    def _get_request_json(self, url, headers, post_data=None):
        logging.info("_get_request_json({}, {})".format(url, post_data))
        if post_data:
            res = requests.post(url, headers=headers, json=post_data)
        else:
            res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json()

    def _get_headers(self):
        return {"ClientToken": self._token,
                "Content-Type": "application/json"}


class MockClearMashApi(ClearmashApi):

    def __init__(self):
        super(MockClearMashApi, self).__init__(token="FAKE INVALID TOKEN")

    def get_web_document_system_folder(self, folder_id):
        return {"Folders": [],
                "Items": [{"Id": (folder_id*100+i)} for i in range(1, 50)]}

    def get_documents(self, entity_ids):
        response = {}
        with open(os.path.join(os.path.dirname(__file__), "mock_data",
                               "clearmash-api-documents-get-115325-115353-115365-115371-115388-265694.json")) as f:
            mock_response = json.load(f)
        response["ReferencedDatasourceItems"] = mock_response["ReferencedDatasourceItems"]
        response["Entities"] = []
        infinite_entities = cycle(mock_response["Entities"])
        for entity_id in entity_ids:
            folder_id = int(entity_id / 100)
            entity = deepcopy(next(infinite_entities))
            entity["Document"].update(Id="foobarbaz-{}".format(entity_id),
                                      TemplateReference={"ChangesetId": folder_id*3,
                                                         "TemplateId": "fake-template-{}".format(folder_id)})
            entity["Metadata"].update(Id=entity_id, Url="http://foo.bar.baz/{}".format(entity_id))
            response["Entities"].append(entity)
        return response

    def _get_mock_request_filename(self, url, headers, post_data):
        if url == "https://bh.clearmash.com/API/V5/Services/WebContentManagement.svc/Document/ByRelationField":
            return "clearmash-api-get-related-docs-by-item-field-220590.json"
        else:
            return None

    def _get_request_json(self, url, headers, post_data=None):
        filename = self._get_mock_request_filename(url, headers, post_data)
        if not filename:
            return super(MockClearMashApi, self)._get_request_json(url, headers, post_data)
        else:
            with open(os.path.join(os.path.dirname(__file__), "mock_data", filename)) as f:
                return json.load(f)

from .constants import WCM_BASE_URL, FOLDER_TYPE_WebDocumentSystemFolder
from datapackage_pipelines_mojp import settings
import requests
from pyquery import PyQuery as pq
import os, json
from itertools import cycle
from copy import deepcopy
import logging
import datetime


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
    return parsed_doc

def parse_clearmash_document_field(document_field):
    allowed_groups = document_field.pop("AllowedGroups")
    value = document_field.pop("Value")
    assert len(document_field) == 0, "unknown attributes in document field: {}".format(document_field.keys())
    assert len(document_field) == 0, "cannot handle allowed_groups in document field: {}".format(allowed_groups)
    return {"document_id": value.pop("Id"),
            "template_reference": value.pop("TemplateReference"),
            "doc": parse_clearmash_document(value, [])}



class ClearmashStartDate(object):
    
    def __init__(self, field_id, date_parameters):
        self.field_id = field_id
        self.date_parameters = date_parameters

    def get_iso_date(self):
        val = self.date_parameters.pop("Value")
        val_dates = val.pop("Value")
        datedata = val_dates.pop("ReducedAccuracyDate")
        info = []
        for k in datedata:
            if k == "DayNumberOfMonth":
                day = datedata[k]
                info.append(day)
            elif k == "MonthNumberOfYear":
                month = datedata[k]
                info.append(month)
            elif k == "YearNumber":
                year = datedata[k]
                info.append(year)

        if len(info) == 1:
            date = "1 1 {}".format(info[0])
        elif len(info) == 2:
            date = "1 {} {}".format(info[0], info[1])
        elif len(info) == 3:
            date = "{} {} {}".format(info[0], info[1], info[2])

        test_date = datetime.datetime.strptime(date, '%d %m %Y').isoformat()
        return "{}Z".format(test_date)
       

class ClearmashRelatedDocuments(object):
    
    def __init__(self, first_page_results, entity_id, field_name, total_count):
        self.first_page_results = first_page_results
        self.total_count = total_count
        self.entity_id = entity_id
        self.field_name = field_name

    def get_clearmash_api(self):
        return ClearmashApi()

    @classmethod
    def get_for_doc(cls, doc):
        res = {}
        entity_id = doc["item_id"]
        for k,v in doc["parsed_doc"].items():
            if isinstance(v, (tuple, list)) and len(v) == 2 and v[0] == "RelatedDocuments":
                first_page = v[1]["FirstPageOfReletedDocumentsIds"]
                field_name = v[1]["Id"]
                total_count = v[1]["TotalItemsCount"]
                res[field_name] = cls(first_page, entity_id, field_name, total_count)
        return res

    def get_related_documents(self):
        if len(self.first_page_results) > 0:
            related_documents = self.get_clearmash_api().get_document_related_docs_by_fields(self.entity_id,
                                                                                             self.field_name)
            return parse_clearmash_documents(related_documents)
        else:
            return []


class ClearmashChildDocuments(object):

    def __init__(self, parsed_doc, document_id, template_reference):
        self.parsed_doc = parsed_doc
        self.document_id = document_id
        self.template_reference = template_reference

    def get_clearmash_api(self):
        return ClearmashApi()

    @classmethod
    def get_for_doc(cls, doc):
        res = {}
        for k, v in doc["parsed_doc"].items():
            if isinstance(v, (tuple, list)) and len(v) == 2 and v[0] == "ChildDocuments":
                field = v[1]
                field_id = field.pop("Id")
                res[field_id] = []
                child_documents = field.pop("ChildDocuments")
                assert len(field) == 0, "unknown attributes in ChildDocuments field: {}".format(field.keys())
                for child_document in child_documents:
                    child_doc = parse_clearmash_document_field(child_document)
                    res[field_id].append(cls(child_doc["doc"],
                                             child_doc["document_id"],
                                             child_doc["template_reference"]))
        return res

class ClearmashMediaGalleries(object):

    def __init__(self, field_id, gallery_items, gallery_main_document):
        self.gallery_items = gallery_items
        self.gallery_main_document = gallery_main_document
        self.field_id = field_id

    def get_clearmash_api(self):
        return ClearmashApi()

    @classmethod
    def get_for_parsed_doc(cls, parsed_doc):
        res = {}
        for k, v in parsed_doc.items():
            if isinstance(v, (tuple, list)) and len(v) == 2 and v[0] == "MediaGalleries":
                field = v[1]
                field_id = field.pop("Id")
                res[field_id] = []
                galleries = field.pop("Galleries")
                assert len(field) == 0, "unknown attributes in MediaGalleries field: {}".format(field.keys())
                for gallery in galleries:
                    gallery_items = []
                    for gallery_item in gallery.pop("GalleryItems"):
                        media_urls = {}
                        for k in list(gallery_item.keys()):
                            if k.startswith("MediaUrl_"):
                                v = gallery_item.pop(k)
                                media_urls[k.replace("MediaUrl_", "")] = v
                        item_document = gallery_item.pop("ItemDocument")
                        gallery_items.append({
                            "__type": gallery_item.pop("__type"),
                            "ItemDocument": parse_clearmash_document_field(item_document),
                            "PosterImageUrl": gallery_item.pop("PosterImageUrl"),
                            "MediaUrls": media_urls
                        })
                        assert len(gallery_item) == 0
                    gallery_main_document = parse_clearmash_document_field(gallery.pop("GalleryMainDocument"))
                    assert len(gallery) == 0
                    res[field_id].append(cls(field_id, gallery_items, gallery_main_document))
        return res

    @classmethod
    def get_for_child_doc(cls, child_doc):
        return cls.get_for_parsed_doc(child_doc.parsed_doc)



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

import json
from datapackage_pipelines_mojp.common.processors.base_processors import BaseDownloadProcessor
from datapackage_pipelines_mojp.clearmash.api import ClearmashApi, MockClearMashApi, parse_clearmash_document
from datapackage_pipelines_mojp.clearmash.constants import (CONTENT_FOLDERS, DOWNLOAD_TABLE_SCHEMA,
                                                            ITEM_IDS_BUFFER_LENGTH)


class ClearmashDownloadProcessor(BaseDownloadProcessor):

    def __init__(self, *args, **kwargs):
        self.clearmash_api = None
        super(ClearmashDownloadProcessor, self).__init__(*args, **kwargs)

    def _get_clearmash_api(self):
        return ClearmashApi()

    def _get_mock_clearmash_api(self):
        return MockClearMashApi()

    def _get_source_name(self):
        return "clearmash"

    def _get_schema(self):
        return DOWNLOAD_TABLE_SCHEMA

    def _download(self, clearmash_api=None):
        if not clearmash_api:
            clearmash_api = self._get_clearmash_api()
        for folder_id, folder in CONTENT_FOLDERS.items():
            self.item_ids_buffer = []
            for item in clearmash_api.get_web_document_system_folder(folder_id)["Items"]:
                self.item_ids_buffer.append(item["Id"])
                yield from self._handle_item_ids_buffer(folder, clearmash_api)
            yield from self._handle_item_ids_buffer(folder, clearmash_api, force_flush=True)

    def _mock_download(self):
        yield from self._download(clearmash_api=self._get_mock_clearmash_api())

    def _handle_item_ids_buffer(self, folder, clearmash_api, force_flush=False):
        if force_flush or len(self.item_ids_buffer) > ITEM_IDS_BUFFER_LENGTH:
            documents_response = clearmash_api.get_documents(self.item_ids_buffer)
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
                       "metadata": json.dumps(metadata),
                       "parsed_doc": json.dumps(parsed_doc),
                       "changeset": int(entity.pop("Changeset")),
                       "collection": folder["collection"]}
            self.item_ids_buffer = []


if __name__ == '__main__':
    ClearmashDownloadProcessor.main()

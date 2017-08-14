from datapackage_pipelines_mojp.common.constants import DBS_DOCS_TABLE_SCHEMA
from datapackage_pipelines_mojp.clearmash.constants import CLEARMASH_SOURCE_ID
from datapackage_pipelines_mojp.clearmash.api import ClearmashApi, ClearmashRelatedDocuments
from datapackage_pipelines_mojp.common.processors.base_processors import BaseProcessor
from datapackage_pipelines_mojp.common.utils import populate_iso_639_language_field
from datapackage_pipelines_mojp.clearmash.common import doc_show_filter
import logging


class Processor(BaseProcessor):

    @classmethod
    def _get_schema(self):
        return DBS_DOCS_TABLE_SCHEMA

    def _filter_resource(self, resource_descriptor, resource_data):
        related_documents_config = self._parameters.get("related-documents")
        if related_documents_config:
            self._related_documents_db_table = self.db_meta.tables.get(related_documents_config["table"])
            self._related_documents_item_id_col = getattr(self._related_documents_db_table.c,
                                                          related_documents_config["item-id-column"])
            self._related_documents_document_id_col = getattr(self._related_documents_db_table.c,
                                                              related_documents_config["document-id-column"])
        else:
            self._related_documents_db_table = None
        self._stats["num_converted_rows"] = 0
        self._stats["num_rows_not_allowed"] = 0
        for cm_row in resource_data:
            dbs_row = self._cm_row_to_dbs_row(cm_row)
            if self._doc_show_filter(dbs_row):
                self._add_related_documents(dbs_row, cm_row)
                self._populate_image_fields(dbs_row, cm_row)
                self._add_geocode_location(dbs_row, cm_row)
                yield dbs_row
                self._stats["num_converted_rows"] += 1
            else:
                self._stats["num_rows_not_allowed"] += 1

    def _get_clearmash_api(self):
        return ClearmashApi()

    def _doc_show_filter(self, dbs_row):
        return doc_show_filter(dbs_row["source_doc"]["parsed_doc"])

    def _get_document_ids(self, cm_row):
        # aggregate all the document ids from all the fields - to allow fetching them from DB in one query
        all_document_ids = []
        # we also build this res which is similar to the res we will return but with document ids instead of item id
        # later we will convert known document ids to item ids
        document_id_res = {}
        for field_id, related_documents in self._get_clearmash_api().related_documents.get_for_doc(cm_row).items():
            document_id_res[field_id] = []
            for document_id in related_documents.first_page_results:
                document_id_res[field_id].append(document_id)
                if document_id not in all_document_ids:
                    all_document_ids.append(document_id)
        return all_document_ids, document_id_res

    def _get_related_doc_item_ids(self, all_document_ids):
        res = {}
        if len(all_document_ids) > 0 and self._related_documents_db_table is not None:
            item_id_col = self._related_documents_item_id_col
            document_id_col = self._related_documents_document_id_col
            rows = self.db_session.query(item_id_col, document_id_col).filter(document_id_col.in_(all_document_ids)).all()
            res = {row[1]: row[0] for row in rows}
        return res

    def _get_related_documents(self, cm_row):
        all_document_ids, document_id_res = self._get_document_ids(cm_row)
        item_ids = self._get_related_doc_item_ids(all_document_ids)
        res = {}
        for field_id, related_document_ids in document_id_res.items():
            related_item_ids = []
            for document_id in related_document_ids:
                if document_id in item_ids:
                    related_item_ids.append(item_ids[document_id])
            if len(related_item_ids) > 0:
                res[field_id] = ["{}_{}".format(CLEARMASH_SOURCE_ID, item_id) for item_id in related_item_ids]
        return res

    def _get_parsed_docs(self, item_ids):
        table = self._related_documents_db_table
        if table is not None:
            rows = self.db_session.query(table.c.item_id,
                                         table.c.parsed_doc).filter(table.c.display_allowed == True,
                                                                    table.c.item_id.in_(item_ids)).all()
            for row in rows:
                yield {"item_id": row.item_id, "parsed_doc": row.parsed_doc}

    def _get_related_photo_docs_es_ids(self, item_id, related_docs):
        return related_docs.get("_c6_beit_hatfutsot_bh_base_template_multimedia_photos")

    def _related_photo_parsed_docs(self, item_id, related_docs):
        photo_doc_es_ids = self._get_related_photo_docs_es_ids(item_id, related_docs)
        if photo_doc_es_ids and len(photo_doc_es_ids) > 0:
            item_ids = [es_id.split("_")[1] for es_id in photo_doc_es_ids]
            yield from self._get_parsed_docs(item_ids)

    def _add_related_documents(self, dbs_row, cm_row):
        dbs_row["related_documents"] = self._get_related_documents(cm_row)

    def _cm_row_to_dbs_row(self, cm_row):
        parsed_doc = cm_row["parsed_doc"]
        dbs_row = {"source": CLEARMASH_SOURCE_ID,
                   "id": str(cm_row["item_id"]),
                   "source_doc": cm_row,
                   "version": "{}-{}".format(cm_row["changeset"], cm_row["document_id"]),
                   "collection": self._get_collection(cm_row)}
        populate_iso_639_language_field(dbs_row, "title", parsed_doc.get("entity_name"))
        populate_iso_639_language_field(dbs_row, "content_html", parsed_doc.get("_c6_beit_hatfutsot_bh_base_template_description"))
        return dbs_row

    def _get_collection(self, cm_row):
        return cm_row["collection"]

    def _add_geocode_location(self, dbs_row, cm_row):
        # TODO: for collections other than 'places', get 
        # place from title and/or other fileds (maybe by comparing words in title to list of places?)
        if self._get_collection(cm_row) == "places":
            if dbs_row["title_en"]:
                dbs_row["geo_location"] = dbs_row["title_en"]
            else:
                dbs_row["geo_location"] = ""
        else:
            dbs_row["geo_location"] = ""


    def _get_images_from_parsed_doc(self, item_id, parsed_doc):
        images = []
        all_child_docs = self._get_clearmash_api().child_documents.get_for_parsed_doc(parsed_doc)
        for photo_child_doc in all_child_docs.get("_c6_beit_hatfutsot_bh_photos_multimedia", []):
            media_galleries = self._get_clearmash_api().media_galleries.get_for_child_doc(photo_child_doc)
            for media_gallery in media_galleries.get("_c6_beit_hatfutsot_bh_multimedia_photo_mg", []):
                for gallery_item in media_gallery.gallery_items:
                    media_url = gallery_item["MediaUrl"]
                    if media_url:
                        image_url = media_url.replace("~~st~~", "https://bhfiles.clearmash.com/MediaServer/Images/")
                        tmp = image_url.split(".")
                        images.append({"url": ".".join(tmp[:-1]) + "_1024x1024." + tmp[-1],
                                       "thumbnail_url": ".".join(tmp[:-1]) + "_260x260." + tmp[-1]})
        return images

    def _populate_image_fields(self, dbs_row, cm_row):
        dbs_row["images"] = self._get_images_from_parsed_doc(dbs_row["id"], dbs_row["source_doc"]["parsed_doc"])
        for row in self._related_photo_parsed_docs(cm_row["item_id"], dbs_row["related_documents"]):
            dbs_row["images"] += self._get_images_from_parsed_doc(row["item_id"], row["parsed_doc"])
        dbs_row["main_image_url"], dbs_row["main_thumbnail_image_url"] = "", ""
        if len(dbs_row["images"]) > 0:
            dbs_row["main_image_url"] = dbs_row["images"][0]["url"]
            dbs_row["main_thumbnail_image_url"] = dbs_row["images"][0]["thumbnail_url"]


if __name__ == '__main__':
    Processor.main()

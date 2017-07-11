from datapackage_pipelines_mojp.common.processors.sync import (DBS_DOCS_TABLE_SCHEMA,
                                                               INPUT_RESOURCE_NAME as DBS_DOCS_RESOURCE_NAME)
from datapackage_pipelines_mojp.clearmash.constants import CLEARMASH_SOURCE_ID
from datapackage_pipelines_mojp.common.processors.base_processors import FilterResourcesProcessor
from datapackage_pipelines_mojp.common.utils import populate_iso_639_language_field


class ClearmashConvertProcessor(FilterResourcesProcessor):

    def _filter_resource_descriptor(self, descriptor):
        if descriptor["name"] == "clearmash":
            descriptor.update(name=DBS_DOCS_RESOURCE_NAME,
                              path="{}.csv".format(DBS_DOCS_RESOURCE_NAME),
                              schema=DBS_DOCS_TABLE_SCHEMA)
        return descriptor

    def _doc_show_filter(self, dbs_row):
        return bool(dbs_row["source_doc"]["parsed_doc"].get('_c6_beit_hatfutsot_bh_base_template_working_status')[0].get("en") == 'Completed'
                    and dbs_row["source_doc"]["parsed_doc"].get('_c6_beit_hatfutsot_bh_base_template_rights')[0].get("en") == 'Full'
                    and dbs_row["source_doc"]["parsed_doc"].get('_c6_beit_hatfutsot_bh_base_template_display_status')[0].get("en") not in ['Internal Use'])

    def _filter_row(self, row, resource_descriptor):
        if resource_descriptor["name"] == DBS_DOCS_RESOURCE_NAME:
            dbs_row = self._cm_row_to_dbs_row(row)
            if self._doc_show_filter(dbs_row):
                return dbs_row
            else:
                return None
        else:
            return row

    def _cm_row_to_dbs_row(self, cm_row):
        parsed_doc = cm_row["parsed_doc"]
        dbs_row = {"source": CLEARMASH_SOURCE_ID,
                   "id": str(cm_row["item_id"]),
                   "source_doc": cm_row,
                   "version": "{}-{}".format(cm_row["changeset"], cm_row["document_id"]),
                   "collection": self._get_collection(cm_row),
                   "main_image_url": "",
                   "main_thumbnail_image_url": ""}
        populate_iso_639_language_field(dbs_row, "title", parsed_doc.get("entity_name"))
        populate_iso_639_language_field(dbs_row, "content_html", parsed_doc.get("_c6_beit_hatfutsot_bh_base_template_description"))
        return dbs_row

    def _get_collection(self, cm_row):
        return cm_row["collection"]


if __name__ == '__main__':
    ClearmashConvertProcessor.main()

import json
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

    def _filter_row(self, row, resource_descirptor):
        return self._cm_row_to_dbs_row(row) if resource_descirptor["name"] == DBS_DOCS_RESOURCE_NAME else row

    def _cm_row_to_dbs_row(self, cm_row):
        parsed_doc = json.loads(cm_row["parsed_doc"])
        dbs_row = {"source": CLEARMASH_SOURCE_ID,
                   "id": str(cm_row["item_id"]),
                   "source_doc": json.dumps(cm_row),
                   "version": "{}-{}".format(cm_row["changeset"], cm_row["document_id"]),
                   "collection": self._get_collection(cm_row)}
        populate_iso_639_language_field(dbs_row, "title", parsed_doc.get("entity_name"))
        populate_iso_639_language_field(dbs_row, "content_html", parsed_doc.get("_c6_beit_hatfutsot_bh_base_template_description"))
        return dbs_row

    def _get_collection(self, cm_row):
        return cm_row["collection"]


if __name__ == '__main__':
    ClearmashConvertProcessor.main()

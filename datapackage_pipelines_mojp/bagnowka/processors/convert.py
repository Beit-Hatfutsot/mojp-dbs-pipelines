# datapackage_pipelines_mojp/bagnowka/convert.py

from datapackage_pipelines_mojp.common.constants import DBS_DOCS_TABLE_SCHEMA
from datapackage_pipelines_mojp.common.processors.base_processors import BaseProcessor
from datapackage_pipelines_mojp.common.utils import populate_iso_639_language_field
import logging


class BagnowkaConvertProcessor(BaseProcessor):

    @classmethod
    def _get_schema(self):
        return DBS_DOCS_TABLE_SCHEMA

    def _filter_resource(self, resource_descriptor, resource_data):
        for bagnowka_row in resource_data:
            dbs_row = self.bagnowka_row_to_dbs_row(bagnowka_row)
            yield dbs_row

    def bagnowka_row_to_dbs_row(self, bagnowka_row):

        dbs_row = {"source": "Bagnowka",
                   "id": bagnowka_row["id"],
                   "version": "one",
                   "title": {},
                   "collection": "photoUnits",
                   "main_image_url": bagnowka_row["main_image_url"],
                   "main_thumbnail_image_url": bagnowka_row["main_thumbnail_url"],
                   "title_en": bagnowka_row["name"],
                   "title_he": "",
                   "content_html": {},
                   "content_html_en": bagnowka_row["desc"],
                   "content_html_he": "",
                   "related_documents": {},
                   "source_doc": bagnowka_row,
                   "images": bagnowka_row["pictures"],
                   "geo_location": ""
                   }
        return dbs_row


if __name__ == '__main__':
    BagnowkaConvertProcessor.main()

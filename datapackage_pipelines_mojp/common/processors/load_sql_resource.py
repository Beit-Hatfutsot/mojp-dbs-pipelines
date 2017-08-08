from datapackage_pipelines_mojp.common.processors.base_processors import BaseProcessor
from datapackage_pipelines_mojp.common.utils import parse_import_func_parameter
import json
import logging
from sqlalchemy import *


class LoadSqlResource(BaseProcessor):

    def _process(self, *args, **kwargs):
        self._db_table = self.db_meta.tables.get(
            self._parameters["load-table"])
        return super(LoadSqlResource, self)._process(*args, **kwargs)

    def _get_schema(self):
        schema = self._parameters.get("schema")
        if schema:
            self._schema = parse_import_func_parameter(schema)
            return self._schema
        else:
            with open(self._parameters["datapackage"]) as f:
                for resource in json.load(f)["resources"]:
                    if resource["name"] == self._parameters["load-resource"]:
                        self._schema = resource["schema"]
                        return self._schema

    def _get_id_column(self):
        primary_keys = self._schema.get("primaryKey")
        if primary_keys and len(primary_keys) == 1:
            return getattr(self._db_table.c, primary_keys[0])
        else:
            raise Exception(
                "failed to find an appropriate primary key in the schema")

    def _get_resource(self):
        if self._db_table is not None:
            self._id_column = self._get_id_column()
            self._where = parse_import_func_parameter(
                self._parameters.get("where"))
            query = self.db_session.query(self._id_column)
            if self._where:
                query = query.filter(text(self._where))
            all_ids = [getattr(row, self._id_column.name)
                       for row in query.all()]
            num_total = len(all_ids)
            batch_size = 10
            num_rows = 0
            for i in range(0, num_total, batch_size):
                ids = all_ids[i:i + batch_size]
                for db_row in self.db_session.query(self._db_table).filter(self._id_column.in_(ids)).all():
                    row = {}
                    for field in self._schema["fields"]:
                        val = getattr(db_row, field["name"])
                        row[field["name"]] = val
                    yield row
                    num_rows += 1
                if i > 0 and i % 500 == 0:
                    logging.info("loaded {} / {}".format(i, num_total))
            logging.info("loaded {} / {}".format(num_rows, num_total))
            self._stats["load_sql_resource_num_rows_yielded"] = num_rows


if __name__ == '__main__':
    LoadSqlResource.main()

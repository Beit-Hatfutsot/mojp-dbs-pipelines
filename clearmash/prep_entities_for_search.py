from datapackage_pipelines.wrapper import ingest, spew
from datapackage_pipelines.utilities.resources import PROP_STREAMING
from bs4 import BeautifulSoup


parameters, datapackage, resources = ingest()


def get_resource():
    for resource in resources:
        for row in resource:
            if row["collection"] == parameters["collection-name"] and row["display_allowed"]:
                doc = row["parsed_doc"]
                item = {"doc_id": "clearmash_{}".format(row["id"]),
                        "source": "clearmash",
                        "collection": parameters["collection-name"],
                        "title_he": doc.get("entity_name", {}).get("he", ""),
                        "title_en": doc.get("entity_name", {}).get("en", ""),
                        "content_html_he": doc.get("_c6_beit_hatfutsot_bh_base_template_description", {}).get("he", ""),
                        "content_html_en": doc.get("_c6_beit_hatfutsot_bh_base_template_description", {}).get("en", "")}
                item.update(content_text_he=' '.join(BeautifulSoup(item["content_html_he"], "lxml").findAll(text=True)),
                            content_text_en=' '.join(BeautifulSoup(item["content_html_en"], "lxml").findAll(text=True)))
                yield item


datapackage["resources"] = [{PROP_STREAMING: True,
                             "name": parameters["resource-name"],
                             "path": "{}.csv".format(parameters["resource-name"]),
                             "schema": {"fields": [{'name': 'doc_id', 'type': 'string', 'es:index': False},
                                                   {"name": "source", "type": "string", "es:index": False},
                                                   {"name": "collection", "type": "string", "es:index": False},
                                                   {"name": "title_he", "type": "string"},
                                                   {"name": "title_en", "type": "string"},
                                                   {"name": "content_html_he", "type": "string", "es:index": False},
                                                   {"name": "content_html_en", "type": "string", "es:index": False},
                                                   {"name": "content_text_he", "type": "string"},
                                                   {"name": "content_text_en", "type": "string"},],
                                        "primaryKey": ["doc_id"]}}]

spew(datapackage, [get_resource()])

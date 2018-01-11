import logging, sys, os, json
from datapackage_pipelines.wrapper import ingest, spew
from datapackage_pipelines.utilities.resources import PROP_STREAMING
from datapackage_pipelines_mojp.clearmash.api import ClearmashApi


FIELDS = (("community_id", "CommunityId", "integer"),
          ("creator_person_id", "CreatorPersonId", "integer"),
          ("file_type", "FileType", "integer"),
          ("id", "Id", "integer"),
          ("is_bookmarked", "IsBookmarked", "boolean"),
          ("is_folder", "IsFolder", "boolean"),
          ("is_liked", "IsLiked", "boolean"),
          ("is_published", "IsPublished", "boolean"),
          ("is_readonly", "IsReadOnly", "boolean"),
          ("is_searchable", "IsSearchable", "boolean"),
          ("likes_count", "LikesCount", "integer"),
          ("locked_by_person_id", "LockedByPersonId", "integer"),
          ("locked_by_person_name", "LockedByPersonName", "string"),
          ("modified_by_person_id", "ModifiedByPersonId", "integer"),
          ("modified_by_person_name", "ModifiedByPersonName", "string"),
          ("name", "Name", "string"),
          ("parent_folder_id", "ParentFolderId", "integer"),
          ("permission_type", "PermissionType", "integer"),
          ("size_in_bytes", "SizeInBytes", "integer"),
          ("user_can_publish", "UserCanPublish", "boolean"),)


CLI_MODE = len(sys.argv) > 1 and sys.argv[1] == '--cli'


if CLI_MODE:
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    logging.debug("CLI MODE!")
    parameters, datapackage, resources = {}, {}, []
else:
    parameters, datapackage, resources = ingest()


parameters = dict({"max-recursion-depth": int(os.environ.get("MAX_RECURSION_DEPTH", "-1"))}, **parameters)
logging.info(parameters)
stats = {}
aggregations = {"stats": stats, "error_folder_ids": set()}


api = ClearmashApi()


def get_folder_row(folder):
    return {r: folder[o] for r, o, t in FIELDS}


def get_row(source_row, parent_folder_names=None, parent_folder_ids=None):
    row = {r: source_row[o] for r, o, t in FIELDS}
    row.update(parent_folder_names=parent_folder_names, parent_folder_ids=parent_folder_ids)
    return row


def get_folder_items(folder_id, recursion_depth=0, recursion_folders=None):
    recursion_folders = [] if not recursion_folders else recursion_folders
    parent_folder_names, parent_folder_ids = None, None
    if len(recursion_folders) > 0:
        parent_folder_names = ">".join([folder["Name"] for folder in recursion_folders])
        parent_folder_ids = ">".join([str(folder["Id"]) for folder in recursion_folders])
    if recursion_depth > 2:
        logging.info("reucrsion depth = {}, parent_folder_names = {}".format(recursion_depth, parent_folder_names))
    try:
        doc = api.get_web_document_system_folder(folder_id)
        for item in doc["Items"]:
            yield get_row(item, parent_folder_names, parent_folder_ids)
        for folder in doc["Folders"]:
            yield get_row(folder, parent_folder_names, parent_folder_ids)
            if parameters["max-recursion-depth"] == -1 or recursion_depth < parameters["max-recursion-depth"]:
                yield from get_folder_items(folder["Id"], recursion_depth + 1, recursion_folders + [folder])
            else:
                logging.warning("Reached folders max recursion depth")
    except Exception:
        logging.exception("failed to get web document system folder {}".format(folder_id))
        aggregations["error_folder_ids"].add(int(folder_id))



def get_resource():
    for folder in api.get_documents_root_folders():
        yield get_row(folder)
        yield from get_folder_items(folder["Id"], 0, [folder])
    logging.error("failed folder ids: {}".format(", ".join(map(str, aggregations["error_folder_ids"]))))


if CLI_MODE:
    if "--root" in sys.argv:
        for folder in api.get_documents_root_folders():
            print(folder)
    else:
        folder_ids = list(map(int, sys.argv[2].split(","))) if len(sys.argv) > 2 else None
        if folder_ids:
            print("folder_ids={}".format(folder_ids))
            for folder_id in folder_ids:
                for item in get_folder_items(folder_id):
                    print(item)
        else:
            for item in get_resource():
                print(item)
else:
    entity_ids_resource = {PROP_STREAMING: True,
                           "name": "entity-ids",
                           "path": "entity-ids.csv",
                           "schema": {"fields": [{"name": r, "type": t} for r, o, t in FIELDS]}}
    entity_ids_resource["schema"]["fields"] += [{"name": "parent_folder_names", "type": "string"},
                                                {"name": "parent_folder_ids", "type": "string"}]
    spew(dict(datapackage, resources=[entity_ids_resource]),
         [get_resource()], aggregations["stats"])

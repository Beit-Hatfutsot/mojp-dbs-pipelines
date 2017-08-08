COLLECTION_UNKNOWN = "unknown"
COLLECTION_PLACES = "places"
COLLECTION_FAMILY_NAMES = "familyNames"
COLLECTION_MOVIES = "movies"
COLLECTION_PERSONALITIES = "personalities"
COLLECTION_PHOTOUNITS = "photoUnits"
ALL_KNOWN_COLLECTIONS = [COLLECTION_PLACES, COLLECTION_FAMILY_NAMES, COLLECTION_MOVIES,
                         COLLECTION_PERSONALITIES, COLLECTION_PHOTOUNITS]

SLUG_LANGUAGES_MAP = {
    COLLECTION_PLACES: {'en': 'place', 'he': u'מקום',},
    COLLECTION_FAMILY_NAMES: {'en': 'familyname', 'he': u'שםמשפחה',},
    COLLECTION_PHOTOUNITS: {'en': 'image', 'he': u'תמונה',},
    COLLECTION_PERSONALITIES: {'en': 'luminary', 'he': u'אישיות',},
    COLLECTION_MOVIES: {'en': 'video', 'he': u'וידאו',},
}

PIPELINES_ES_DOC_TYPE = "common"

# suggest works only for these languages
# pipelines ensure it enters a value to the "title_{lang}_suggest" field
SUPPORTED_SUGGEST_LANGS = ["he", "en"]

COLLECTION_FIELD_DESCRIPTION = "standard collection identifier (e.g. places / familyNames etc..). " \
                               "must be related to one of the COLLECTION_? constants"

DBS_DOCS_TABLE_SCHEMA = {"fields": [{"name": "source", "type": "string"},
                                    {'name': 'id', 'type': 'string'},
                                    {"name": "version", "type": "string",
                                     "description": "source dependant field, used by sync process to detect document updates"},
                                    {"name": "collection", "type": "string",
                                        "description": COLLECTION_FIELD_DESCRIPTION},
                                    {"name": "source_doc", "type": "object"},
                                    {"name": "title", "type": "object",
                                    "description": "languages other then he/en, will be flattened on elasticsearch to content_html_LANG"},
                                    {"name": "title_he", "type": "string"},
                                    {"name": "title_en", "type": "string"},
                                    {"name": "content_html", "type": "object",
                                     "description": "languages other then he/en, will be flattened on elasticsearch to content_html_LANG"},
                                    {"name": "content_html_he", "type": "string"},
                                    {"name": "content_html_en", "type": "string"},
                                    {"name": "main_image_url", "type": "string",
                                     "description": "url to the main image"},
                                    {"name": "main_thumbnail_image_url", "type": "string",
                                     "description": "url to the main thumbnail image"},
                                    {"name": "related_documents", "type": "object",
                                     "description": "related documents of different types (source-specific)"},
                                    {"name": "images", "type": "array"},]}

DBS_DOCS_SYNC_LOG_TABLE_SCHEMA = {"fields": [{"name": "source", "type": "string"},
                                             {'name': 'id', 'type': 'string'},
                                             {"name": "version", "type": "string",
                                              "description": "source dependant field, used by sync process to detect document updates"},
                                             {"name": "collection", "type": "string",
                                                 "description": COLLECTION_FIELD_DESCRIPTION},
                                             {"name": "sync_msg", "type": "string"}]}

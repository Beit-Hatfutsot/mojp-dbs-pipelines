from datapackage_pipelines_mojp.common import constants as common_constants

WCM_BASE_URL = "https://bh.clearmash.com/API/V5/Services/WebContentManagement.svc"

# the identifier of this source in the BH databases
# each data source has a unique id
CLEARMASH_SOURCE_ID = "clearmash"

# hard-coded in the wsdl definition (might need to update if more types will be added by ClearMash)
FOLDER_TYPE_Root = -1
FOLDER_TYPE_MultipleItems = 0
FOLDER_TYPE_CommunityPageSystemFolder = 1
FOLDER_TYPE_CommunityPageFolder = 2
FOLDER_TYPE_CommunityPage = 3
FOLDER_TYPE_WebDocumentSystemFolder = 4
FOLDER_TYPE_WebDocumentFolder = 5
FOLDER_TYPE_WebDocument = 6
FOLDER_TYPE_TemplateSystemFolder = 7
FOLDER_TYPE_TemplateFolder = 8
FOLDER_TYPE_Template = 9
FOLDER_TYPE_TemplateCustomControlSystemFolder = 10
FOLDER_TYPE_TemplateCustomControlFolder = 11
FOLDER_TYPE_TemplateCustomControl = 12
FOLDER_TYPE_ReportPageSystemFolder = 13
FOLDER_TYPE_ReportPageFolder = 14
FOLDER_TYPE_ReportPage = 15

# see tests.test_clearmash_api.test_get_documents_root_folders
WEB_CONTENT_FOLDER_ID_Movies = 40  # סרטים  --> 'movies',
# WEB_CONTENT_FOLDER_ID_Music = 41  #: 'מוסיקה',
WEB_CONTENT_FOLDER_ID_Photos = 42  #: 'תמונות',  --> 'photoUnits',
WEB_CONTENT_FOLDER_ID_Place = 43  #: 'מקום', --> 'places',
# WEB_CONTENT_FOLDER_ID_Family = 44  #: 'משפחה',
WEB_CONTENT_FOLDER_ID_FamilyName = 45  #: 'שם משפחה',  --> 'familyNames',
# WEB_CONTENT_FOLDER_ID_Exhibition = 46  #: 'תערוכה',
# WEB_CONTENT_FOLDER_ID_Music_Text = 47  #: 'מוסיקה טקסט',
# 48: 'יחידת קבלה',
WEB_CONTENT_FOLDER_ID_Personality = 49  #: 'אישיות',  --> 'personalities',
# 50: 'ערך',
# WEB_CONTENT_FOLDER_ID_Family_Tree = 51  #: 'עץ משפחה',
# 53: 'מקור'

CONTENT_FOLDERS = {
    WEB_CONTENT_FOLDER_ID_FamilyName: {"collection": common_constants.COLLECTION_FAMILY_NAMES},
    WEB_CONTENT_FOLDER_ID_Place: {"collection": common_constants.COLLECTION_PLACES},
    WEB_CONTENT_FOLDER_ID_Movies: {"collection": common_constants.COLLECTION_MOVIES},
    WEB_CONTENT_FOLDER_ID_Personality: {"collection": common_constants.COLLECTION_PERSONALITIES},
    WEB_CONTENT_FOLDER_ID_Photos: {"collection": common_constants.COLLECTION_PHOTOUNITS},
}

DOWNLOAD_TABLE_SCHEMA = {"fields": [{"name": "document_id", "type": "string",
                                     "description": "some sort of internal GUID"},
                                    {"name": "item_id", "type": "integer",
                                     "description": "the item id as requested from the folder"},
                                    {"name": "item_url", "type": "string",
                                     "description": "url to view the item in CM"},
                                    {"name": "collection", "type": "string",
                                     "description": "common dbs docs collection string"},
                                    {"name": "template_changeset_id", "type": "integer",
                                     "description": "I guess it's the id of template when doc was saved"},
                                    {"name": "template_id", "type": "string",
                                     "description": "can help to identify the item type"},
                                    {"name": "changeset", "type": "integer",
                                     "description": ""},
                                    {"name": "metadata", "type": "string",
                                     "description": "json of remaining unparsed attribute"},
                                    {"name": "parsed_doc", "type": "string",
                                     "description": "json of remaining unparsed attribute"}]}

ITEM_IDS_BUFFER_LENGTH = 10

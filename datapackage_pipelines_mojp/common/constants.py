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

# suggest works only for these languages
# pipelines ensure it enters a value to the "title_{lang}_suggest" field
SUPPORTED_SUGGEST_LANGS = ["he", "en"]

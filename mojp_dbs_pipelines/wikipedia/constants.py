# temporarily - we hard-code the page titles to download
WIKIPEDIA_PAGES_TO_DOWNLOAD = {
    "he": [
        "פייבל_פולקס",
        "דוד_בן-גוריון"
    ],
    "en": [
        "Merneptah_Stele",
        "Thebes,_Egypt"
    ]
}

WIKIPEDIA_PARSE_API_URL_TEMPLATE = "https://{language}.wikipedia.org/w/api.php?action=parse&page={page_title}&format=json"

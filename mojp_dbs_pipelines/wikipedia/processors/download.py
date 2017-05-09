from mojp_dbs_pipelines.common.processors.base_processors import AddResourcesProcessor
import json
from mojp_dbs_pipelines.wikipedia.constants import WIKIPEDIA_PAGES_TO_DOWNLOAD, WIKIPEDIA_PARSE_API_URL_TEMPLATE
import requests


class WikipediaDownloadProcessor(AddResourcesProcessor):

    def _get_resource_descriptors(self):
        return [{"name": "wikipedia",
                 "path": "wikipedia.csv",
                 "schema": {"fields": [
                     {"name": "id", "type": "integer"},
                     {"name": "source_doc", "type": "string"}
                 ]}}]

    def _get_title_json(self, url):
        return requests.get(url).json()

    def _download_titles(self, lang, titles):
        for title in titles:
            yield from self._download_title(lang, title)

    def _download_title(self, lang, title):
        page = self._get_title_json(WIKIPEDIA_PARSE_API_URL_TEMPLATE.format(language=lang, page_title=title))["parse"]
        yield {"id": page["pageid"], "source_doc": json.dumps(page)}

    def _download(self):
        for lang, titles in WIKIPEDIA_PAGES_TO_DOWNLOAD.items():
            yield from self._download_titles(lang, titles)

    def _get_resources_iterator(self):
        return [self._download()]


if __name__ == '__main__':
    WikipediaDownloadProcessor.main()

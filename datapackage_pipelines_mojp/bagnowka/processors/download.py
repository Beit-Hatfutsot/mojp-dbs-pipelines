# coding:utf8

from datapackage_pipelines_mojp.common.processors.base_processors import BaseProcessor
import json
import logging
import time
import os


class BagnowkaDownloadProcessor(BaseProcessor):

    def __init__(self, *args, **kwargs):
        super(BagnowkaDownloadProcessor, self).__init__(*args, **kwargs)

    @classmethod
    def _get_schema(cls):
        return {"fields": [{"name": "name", "type": "string"},
                           {"name": "main_image_url", "type": "string",
                               "description": "stored in aws S3"},
                           {"name": "main_thumbnail_url", "type": "string",
                               "description": "stored in aws S3"},
                           {"name": "desc", "type": "string"},
                           {"name": "id", "type": "string",
                            "description": "enumerated ID given when scraped"},
                           {"name": "approximate_date_taken", "type": "string",
                            "description": "Date of the photo, extracted from name. "},
                           {"name": "pictures", "type": "array", "description": "List of image & thumbnail urls created by AWS S3"}]}

    def _get_resource(self):
        with open(os.path.join(os.path.dirname(__file__), "bagnowka_all.json")) as f:
            all_docs = json.load(f)
            for item_data in all_docs:
                new = all_docs[item_data]
                doc = self.download(new)
                yield doc

    def download(self, item_data):
        new_doc = {}
        description = item_data["UnitText1"]["En"]
        title = item_data["Header"]["En"]
        main_image_url = item_data["main_image_url"]
        main_id = main_image_url.split('/')
        m_id = main_id[len(main_id) - 1]
        entity_id = item_data["UnitId"]
        date_taken = item_data["PeriodDesc"]["En"]
        new_doc["name"] = title
        new_doc["desc"] = description
        new_doc["main_image_url"] = main_image_url
        new_doc["main_thumbnail_url"] = "https://s3-us-west-2.amazonaws.com/bagnowka-scraped/thumbs/small/{}".format(
            m_id)
        new_doc["id"] = entity_id
        new_doc["approximate_date_taken"] = date_taken
        new_doc["pictures"] = self.creat_img_urls(item_data)

        return new_doc

    def creat_img_urls(self, item_data):
        images = []
        all_pics = item_data["Pictures"]
        ids = [i["PictureId"] for i in all_pics]
        full_size_bucket_base_url = "https://s3-us-west-2.amazonaws.com/bagnowka-scraped/full/"
        thumb_bucket_base_url = "https://s3-us-west-2.amazonaws.com/bagnowka-scraped/thumbs/small/"
        for img_id in ids:
            url = "{}{}.jpg".format(full_size_bucket_base_url, img_id)
            thumbnail_url = "{}{}.jpg".format(thumb_bucket_base_url, img_id)
            images.append({'url': url, 'thumbnail_url': thumbnail_url})
        return images

if __name__ == '__main__':
    BagnowkaDownloadProcessor.main()

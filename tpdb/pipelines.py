# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import hashlib

import dateparser
import requests
from pymongo import MongoClient


class TpdbPipeline:
    def process_item(self, item, spider):
        return item


class TpdbApiScenePipeline:
    def __init__(self, crawler):
        # db = MongoClient('mongodb://localhost:27017/')
        # self.db = db['scrapy']
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    async def process_item(self, item, spider):
        ## So we don't re-send scenes that have already been scraped
        # if spider.force is not True:
        #     result = self.db.scenes.find_one({'url': item['url']})
        #     if result is not None:
        #         return

        payload = {
            'title': item['title'],
            'description': item['description'],
            'date': item['date'],
            'image': item['image'],
            'url': item['url'],
            'performers': item['performers'],
            'tags': item['tags'],
            'external_id': str(item['id']),
            'site': item['site'],
            'trailer': item['trailer'],
            'network': item['network']
        }

        headers = {
            "Authorization": "Bearer xxxx",
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'tpdb-scraper/1.0.0'
        }
        ## Post the scene to the API - requires auth with permissions
        # response = requests.post('https://api.metadataapi.net/scenes', json=payload, headers=headers)

        # url_hash = hashlib.sha1(str(item['url']).encode('utf-8')).hexdigest()

        # if response.status_code != 200:
        #     self.db.errors.replace_one({"_id": url_hash}, {
        #         'url': item['url'],
        #         'error': 1,
        #         'when': dateparser.parse('today').isoformat(),
        #         'response': response.json()
        #     }, upsert=True)
        # else:
        #     self.db.scenes.replace_one(
        #         {"_id": url_hash}, dict(item), upsert=True)

        return item

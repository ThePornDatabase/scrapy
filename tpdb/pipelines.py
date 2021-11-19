# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import hashlib
import re
import time
from pathlib import Path

import dateparser
import requests
from pymongo import MongoClient

from scrapy.exporters import JsonItemExporter
from scrapy.exporters import JsonLinesItemExporter


class TpdbPipeline:
    def process_item(self, item, spider):
        return item


class TpdbApiScenePipeline:

    def __init__(self, crawler):
        if crawler.settings['ENABLE_MONGODB']:
            db = MongoClient(crawler.settings['MONGODB_URL'])
            self.db = db['scrapy']

        self.crawler = crawler

        if crawler.settings.get('path'):
            path = crawler.settings.get('path')
        else:
            path = crawler.settings.get('DEFAULT_EXPORT_PATH')

        if crawler.settings.get('file'):
            filename = crawler.settings.get('file')
            if "\\" not in filename and "/" not in filename:
                filename = Path(path, filename)
        else:
            filename = Path(path, crawler.spidercls.name + "_" + time.strftime("%Y%m%d-%H%M") + ".json")

        if crawler.settings.get('export'):
            if crawler.settings.get('export') == 'true':
                print(f"*** Exporting to file: {filename}")
                self.fp = open(filename, 'wb')
                self.fp.write('{"scenes":['.encode())
                if crawler.settings.get('oneline') == 'true':
                    self.exporter = JsonLinesItemExporter(self.fp, ensure_ascii=False, encoding='utf-8')
                else:
                    self.exporter = JsonItemExporter(self.fp, ensure_ascii=False, encoding='utf-8', sort_keys=True, indent=2)
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    async def process_item(self, item, spider):
        if spider.debug is True:
            return item

        # So we don't re-send scenes that have already been scraped
        if self.crawler.settings['ENABLE_MONGODB']:
            if spider.force is not True:
                result = self.db.scenes.find_one({'url': item['url']})
                if result is not None:
                    return

        payload = {
            'title': item['title'],
            'description': item['description'],
            'date': item['date'],
            'image': item['image'],
            'image_blob': item['image_blob'],
            'url': item['url'],
            'performers': item['performers'],
            'tags': item['tags'],
            'external_id': str(item['id']),
            'site': item['site'],
            'trailer': item['trailer'],
            'parent': item['parent'],
            'network': item['network']
        }

        # Post the scene to the API - requires auth with permissions
        if self.crawler.settings['TPDB_API_KEY'] and not spider.settings.get('local'):

            headers = {
                "Authorization": "Bearer " + self.crawler.settings['TPDB_API_KEY'],
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'tpdb-scraper/1.0.0'
            }

            response = requests.post('https://api.metadataapi.net/scenes', json=payload, headers=headers)
            if response:
                if response.status_code == 200:
                    dispresult = "Submitted OK"
                else:
                    dispresult = "Submission Error: Code #" + str(response.status_code)
            else:
                dispresult = "Submission Error: No Response Code"

            url_hash = hashlib.sha1(str(item['url']).encode('utf-8')).hexdigest()

            if self.crawler.settings['MONGODB_ENABLE']:
                if response.status_code != 200:
                    self.db.errors.replace_one({"_id": url_hash}, {
                        'url': item['url'],
                        'error': 1,
                        'when': dateparser.parse('today').isoformat(),
                        'response': response.json()
                    }, upsert=True)
                else:
                    self.db.scenes.replace_one(
                        {"_id": url_hash}, dict(item), upsert=True)
        else:
            dispresult = "Local Run, Not Submitted"

        if spider.settings.get('display') and spider.settings.get('LOG_LEVEL') == "INFO":
            if spider.settings.get('display') == "true":
                if len(item['title']) >= 50:
                    titlelength = 5
                else:
                    titlelength = 55 - len(item['title'])

                if len(item['site']) >= 15:
                    sitelength = 5
                else:
                    sitelength = 20 - len(item['site'])

                if "T" in item['date']:
                    dispdate = re.search(r'(.*)T\d', item['date']).group(1)
                else:
                    dispdate = item['date']

                print(f"Item: {item['title'][0:50]}" + " " * titlelength + f"{item['site'][0:15]}" + " " * sitelength + f"\t{str(item['id'])[0:15]}\t{dispdate}\t{item['url']}\t{dispresult}")

        if spider.settings.get('export'):
            if spider.settings.get('export') == "true":
                item2 = item.copy()
                if not spider.settings.get('showblob'):
                    if "image_blob" in item2:
                        item2.pop('image_blob', None)
                self.exporter.export_item(item2)
        return item

    def close_spider(self, spider):
        if spider.settings.get('export'):
            if spider.settings.get('export') == "true":
                self.fp.write(']}'.encode())
                self.fp.close()


class TpdbApiPerformerPipeline:

    def __init__(self, crawler):
        if crawler.settings['ENABLE_MONGODB']:
            db = MongoClient(crawler.settings['MONGODB_URL'])
            self.db = db['scrapy']

        self.crawler = crawler

        if crawler.settings.get('path'):
            path = crawler.settings.get('path')
        else:
            path = crawler.settings.get('DEFAULT_EXPORT_PATH')

        if crawler.settings.get('file'):
            filename = crawler.settings.get('file')
            if "\\" not in filename and "/" not in filename:
                filename = Path(path, filename)
        else:
            filename = Path(path, crawler.spidercls.name + "_" + time.strftime("%Y%m%d-%H%M") + "-performers.json")

        if crawler.settings.get('export'):
            if crawler.settings.get('export') == 'true':
                print(f"*** Exporting to file: {filename}")
                self.fp = open(filename, 'wb')
                self.fp.write('{"scenes":['.encode())
                if crawler.settings.get('oneline') == 'true':
                    self.exporter = JsonLinesItemExporter(self.fp, ensure_ascii=False, encoding='utf-8')
                else:
                    self.exporter = JsonItemExporter(self.fp, ensure_ascii=False, encoding='utf-8', sort_keys=True, indent=2)


    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    async def process_item(self, item, spider):
        if spider.debug is True:
            return item

        # So we don't re-send scenes that have already been scraped
        if self.crawler.settings['ENABLE_MONGODB']:
            if spider.force is not True:
                result = self.db.performers.find_one({'url': item['url']})
                if result is not None:
                    return

        payload = {
            'name': item['name'],
            'site': item['network'],
            'url': item['url'],
            'image': item['image'],
            'image_blob': item['image_blob'],
            'bio': item['bio'],
            'gender': item['gender'],
            'birthday': item['birthday'],
            'astrology': item['astrology'],
            'birthplace': item['birthplace'],
            'ethnicity': item['ethnicity'],
            'nationality': item['nationality'],
            'eyecolor': item['eyecolor'],
            'haircolor': item['haircolor'],
            'weight': item['weight'],
            'height': item['height'],
            'measurements': item['measurements'],
            'tattoos': item['tattoos'],
            'piercings': item['piercings'],
            'cupsize': item['cupsize'],
            'fakeboobs': item['fakeboobs'],
        }

        # Post the scene to the API - requires auth with permissions
        if self.crawler.settings['TPDB_API_KEY'] and not spider.settings.get('local'):

            headers = {
                "Authorization": "Bearer " + self.crawler.settings['TPDB_API_KEY'],
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'tpdb-scraper/1.0.0'
            }

            response = requests.post('https://api.metadataapi.net/performer_sites', json=payload, headers=headers, verify=False)
            if response:
                if response.status_code == 200:
                    dispresult = "Submitted OK"
                else:
                    dispresult = "Submission Error: Code #" + str(response.status_code)
            else:
                dispresult = "Submission Error: No Response Code"

            url_hash = hashlib.sha1(str(item['url']).encode('utf-8')).hexdigest()

            if self.crawler.settings['MONGODB_ENABLE']:
                if response.status_code != 200:
                    self.db.errors.replace_one({"_id": url_hash}, {
                        'url': item['url'],
                        'error': 1,
                        'when': dateparser.parse('today').isoformat(),
                        'response': response.json()
                    }, upsert=True)
                else:
                    self.db.performers.replace_one({"_id": url_hash}, dict(item), upsert=True)
        else:
            dispresult = "Local Run, Not Submitted"

        if spider.settings.get('display') and spider.settings.get('LOG_LEVEL') == "INFO":
            if spider.settings.get('display') == "true":
                namelength = 50 - len(item['name'])
                if namelength < 1:
                    namelength = 1

                print(f"Performer: {item['name']}" + " " * namelength + f"{item['network']}\t{item['url']}\t{dispresult}")

        if spider.settings.get('export'):
            if spider.settings.get('export') == "true":
                item2 = item.copy()
                if not spider.settings.get('showblob'):
                    if "image_blob" in item2:
                        item2.pop('image_blob', None)
                self.exporter.export_item(item2)
        return item

    def close_spider(self, spider):
        if spider.settings.get('export'):
            if spider.settings.get('export') == "true":
                self.fp.write(']}'.encode())
                self.fp.close()

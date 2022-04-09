# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import hashlib
import json
import re
import time
import zlib
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient
from scrapy.exporters import JsonItemExporter, JsonLinesItemExporter

from tpdb.helpers.http import Http


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
            if '\\' not in filename and '/' not in filename:
                filename = Path(path, filename)
        else:
            filename = Path(path, '%s_%s.json' % (crawler.spidercls.name, time.strftime('%Y%m%d-%H%M')))

        if crawler.settings.getbool('export'):
            print(f'*** Exporting to file: {filename}')
            self.fp = open(filename, 'wb')
            self.fp.write('{"scenes":['.encode())

            if crawler.settings.getbool('oneline'):
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
            'network': item['network'],
            'force_update': self.crawler.settings.getbool('FORCE_UPDATE'),
        }

        # Post the scene to the API - requires auth with permissions
        if self.crawler.settings['TPDB_API_KEY'] and not spider.settings.get('local'):
            headers = {
                'Authorization': 'Bearer %s' % self.crawler.settings['TPDB_API_KEY'],
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Content-Encoding': 'gzip',
                'User-Agent': 'tpdb-scraper/1.0.0'
            }

            payload = zlib.compress(json.dumps(payload).encode('UTF-8'))

            response = Http.post('https://api.metadataapi.net/scenes', data=payload, headers=headers, verify=False)
            if response:
                if response.ok:
                    disp_result = 'Submitted OK'
                else:
                    disp_result = 'Submission Error: Code #%d' % response.status_code
            else:
                disp_result = 'Submission Error: No Response Code'

            url_hash = hashlib.sha1(str(item['url']).encode('utf-8')).hexdigest()

            if self.crawler.settings['MONGODB_ENABLE']:
                if not response.ok:
                    self.db.errors.replace_one({'_id': url_hash}, {
                        'url': item['url'],
                        'error': 1,
                        'when': datetime.now().isoformat(),
                        'response': response.json()
                    }, upsert=True)
                else:
                    self.db.scenes.replace_one(
                        {'_id': url_hash}, dict(item), upsert=True)
        else:
            disp_result = 'Local Run, Not Submitted'

        if spider.settings.getbool('display') and spider.settings.get('LOG_LEVEL') == 'INFO':
            if len(item['title']) >= 50:
                title_length = 5
            else:
                title_length = 55 - len(item['title'])

            if len(item['site']) >= 15:
                site_length = 5
            else:
                site_length = 20 - len(item['site'])

            if "T" in item['date']:
                disp_date = re.search(r'(.*)T\d', item['date']).group(1)
            else:
                disp_date = item['date']

            print(f"Item: {item['title'][0:50]}" + " " * title_length + f"{item['site'][0:15]}" + " " * site_length + f"\t{str(item['id'])[0:15]}\t{disp_date}\t{item['url']}\t{disp_result}")

        if spider.settings.getbool('export'):
            item2 = item.copy()
            if not spider.settings.get('showblob'):
                if 'image_blob' in item2:
                    item2.pop('image_blob', None)
            self.exporter.export_item(item2)

        return item

    def close_spider(self, spider):
        if spider.settings.getbool('export'):
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
            if '\\' not in filename and '/' not in filename:
                filename = Path(path, filename)
        else:
            filename = Path(path, '%s_%s-performers.json' % (crawler.spidercls.name, time.strftime('%Y%m%d-%H%M')))

        if crawler.settings.getbool('export'):
            print(f"*** Exporting to file: {filename}")
            self.fp = open(filename, 'wb')
            self.fp.write('{"scenes":['.encode())

            if crawler.settings.getbool('oneline'):
                self.exporter = JsonLinesItemExporter(self.fp, ensure_ascii=False, encoding='utf-8')
            else:
                self.exporter = JsonItemExporter(self.fp, ensure_ascii=False, encoding='utf-8', sort_keys=True, indent=2)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    async def process_item(self, item, spider):
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
                'Authorization': 'Bearer %s' % self.crawler.settings['TPDB_API_KEY'],
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Content-Encoding': 'gzip',
                'User-Agent': 'tpdb-scraper/1.0.0'
            }

            payload = zlib.compress(json.dumps(payload).encode('UTF-8'))

            response = Http.post('https://api.metadataapi.net/performer_sites', data=payload, headers=headers, verify=False)
            if response:
                if response.ok:
                    disp_result = 'Submitted OK'
                else:
                    disp_result = 'Submission Error: Code #' + str(response.status_code)
            else:
                disp_result = 'Submission Error: No Response Code'

            if self.crawler.settings['MONGODB_ENABLE']:
                url_hash = hashlib.sha1(str(item['url']).encode('utf-8')).hexdigest()
                if not response.ok:
                    self.db.errors.replace_one({'_id': url_hash}, {
                        'url': item['url'],
                        'error': 1,
                        'when': datetime.now().isoformat(),
                        'response': response.json()
                    }, upsert=True)
                else:
                    self.db.performers.replace_one({'_id': url_hash}, dict(item), upsert=True)
        else:
            disp_result = 'Local Run, Not Submitted'

        if spider.settings.getbool('display') and spider.settings.get('LOG_LEVEL') == 'INFO':
            name_length = 50 - len(item['name'])
            if name_length < 1:
                name_length = 1

            print(f"Performer: {item['name']}" + " " * name_length + f"{item['network']}\t{item['url']}\t{disp_result}")

        if spider.settings.getbool('export'):
            item2 = item.copy()
            if not spider.settings.get('showblob'):
                if "image_blob" in item2:
                    item2.pop('image_blob', None)
            self.exporter.export_item(item2)

        return item

    def close_spider(self, spider):
        if spider.settings.getbool('export'):
            self.fp.write(']}'.encode())
            self.fp.close()

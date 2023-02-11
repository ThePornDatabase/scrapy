# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import hashlib
import re
import json
import logging
import time

from pathlib import Path
from datetime import datetime

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

        if crawler.settings.get('FILTER_TAGS'):
            logging.info(f"Loading Scene Tag Alias File: {crawler.settings.get('FILTER_TAG_FILENAME')}")
            with open(crawler.settings.get('FILTER_TAG_FILENAME'), encoding='utf-8') as f:
                self.tagaliases = json.load(f)

        if crawler.settings.get('file'):
            filename = crawler.settings.get('file')
            if '\\' not in filename and '/' not in filename:
                filename = Path(path, filename)
        else:
            filename = Path(path, f'{crawler.spidercls.name}_{time.strftime("%Y%m%d-%H%M")}.json')

        if crawler.settings.getbool('export') or self.crawler.settings['EXPORT_ITEMS']:
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

        if self.crawler.settings['FILTER_TAGS']:
            item['tags'] = self.clean_tags(item['tags'], self.tagaliases)

        if item['date']:
            item['date'] = re.search(r'(\d{4}-\d{2}-\d{2})', item['date']).group(1)

        if "back" not in item:
            item['back'] = ''
        if "back_blob" not in item:
            item['back_blob'] = ''
        if "director" not in item:
            item['director'] = ''
        if "duration" not in item:
            item['duration'] = ''
        if "format" not in item:
            item['format'] = ''
        if "markers" not in item:
            item['markers'] = []
        if "scenes" not in item:
            item['scenes'] = []
        if "sku" not in item:
            item['sku'] = ''
        if "merge_id" not in item:
            item['merge_id'] = ''
        if "store" not in item:
            item['store'] = ''
        if "type" not in item:
            item['type'] = 'Scene'

        item['title'] = item['title'].replace("&amp;", "&")
        item['description'] = item['description'].replace("&amp;", "&")

        payload = {
            'back': item['back'],
            'back_blob': item['back_blob'],
            'date': item['date'],
            'description': item['description'],
            'director': item['director'],
            'duration': item['duration'],
            'external_id': str(item['id']),
            'merge_id': str(item['merge_id']),
            'force_update': self.crawler.settings.getbool('FORCE_UPDATE'),
            'format': item['format'],
            'image': item['image'],
            'image_blob': item['image_blob'],
            'markers': item['markers'],
            'network': item['network'],
            'parent': item['parent'],
            'performers': item['performers'],
            'scenes': item['scenes'],
            'site': item['site'],
            'sku': item['sku'],
            'store': item['store'],
            'tags': item['tags'],
            'title': item['title'],
            'trailer': item['trailer'],
            'type': item['type'],
            'url': item['url'],
        }

        # Post the scene to the API - requires auth with permissions
        disp_result = ""
        if self.crawler.settings['TPDB_API_KEY'] and not spider.settings.get('local'):
            headers = {
                'Authorization': f'Bearer {self.crawler.settings["TPDB_API_KEY"]}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'tpdb-scraper/1.0.0'
            }

            response = Http.post('https://api.metadataapi.net/scenes', json=payload, headers=headers, verify=False, timeout=2)
            if response:
                if response.ok:
                    disp_result = f'{disp_result} Submitted OK'
                else:
                    disp_result = f'{disp_result} Submission Error: Code #{response.status_code}'
            else:
                disp_result = f'{disp_result} Submission Error: No Response Code'
                print(response)
                if response:
                    logging.info(response.content)
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

        if spider.settings.get('localdump'):
            # Toss to local TPDB Instance
            headers = {
                'Authorization': f'Bearer {self.crawler.settings["TPDB_TEST_API_KEY"]}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'tpdb-scraper/1.0.0'
            }
            response = Http.post('http://api.tpdb.test/scenes', json=payload, headers=headers)
            if response:
                if response.ok:
                    disp_result = disp_result + '\tSubmitted to Local OK'
                else:
                    disp_result = f'{disp_result} \tSubmission to Local Error: Code #%d{response.status_code}'
            else:
                disp_result = disp_result + '\tSubmission to Local Error: No Response Code'
                if response:
                    logging.info(response.content)
            # #############################

        if (spider.settings.getbool('display') or self.crawler.settings['DISPLAY_ITEMS']) and spider.settings.get('LOG_LEVEL') == 'INFO':
            if len(item['title']) >= 50:
                title_length = 5
            else:
                title_length = 55 - len(item['title'])

            if len(item['site']) >= 15:
                site_length = 5
            else:
                site_length = 20 - len(item['site'])

            if item['date']:
                if "T" in item['date']:
                    disp_date = re.search(r'(.*)T\d', item['date']).group(1)
                else:
                    disp_date = item['date']
            else:
                disp_date = "Calculated"

            logging.info(f"Item: {item['title'][0:50]}" + " " * title_length + f"{item['site'][0:15]}" + " " * site_length + f"\t{str(item['id'])[0:15]}\t{disp_date}\t{item['url']}\t{disp_result}")

        if spider.settings.getbool('export') or self.crawler.settings['EXPORT_ITEMS']:
            item2 = item.copy()
            if not spider.settings.get('showblob'):
                if 'image_blob' in item2:
                    item2.pop('image_blob', None)
                    item2.pop('back_blob', None)
            self.exporter.export_item(item2)

        return item

    def clean_tags(self, tags, aliaslist):
        tags2 = []
        if tags:
            for tag in tags:
                pointer = 0
                for alias in aliaslist:
                    if not pointer and tag.lower().strip() == alias['alias'].lower().strip():
                        tags2.append(alias['tag'])
                        pointer = 1
                        break
                if not pointer:
                    tags2.append(tag.rstrip(".").rstrip(",").strip())

        tags2 = [i for n, i in enumerate(tags2) if i not in tags2[:n]]
        return tags2

    def close_spider(self, spider):
        if spider.settings.getbool('export') or self.crawler.settings['EXPORT_ITEMS']:
            self.fp.write(']}'.encode())
            self.fp.close()


class TpdbApiMoviePipeline:
    def __init__(self, crawler):
        if crawler.settings['ENABLE_MONGODB']:
            db = MongoClient(crawler.settings['MONGODB_URL'])
            self.db = db['scrapy']

        self.crawler = crawler

        if crawler.settings.get('path'):
            path = crawler.settings.get('path')
        else:
            path = crawler.settings.get('DEFAULT_EXPORT_PATH')

        if crawler.settings.get('FILTER_TAGS'):
            logging.info(f"Loading Movie Tag Alias File: {crawler.settings.get('FILTER_TAG_FILENAME')}")
            with open(crawler.settings.get('FILTER_TAG_FILENAME'), encoding='utf-8') as f:
                self.tagaliases = json.load(f)

        if crawler.settings.get('file'):
            filename = crawler.settings.get('file')
            if '\\' not in filename and '/' not in filename:
                filename = Path(path, filename)
        else:
            filename = Path(path, f'{crawler.spidercls.name}_{time.strftime("%Y%m%d-%H%M")}.json')

        if crawler.settings.getbool('export') or self.crawler.settings['EXPORT_ITEMS']:
            print(f'*** Exporting to file: {filename}')
            self.fp = open(filename, 'wb')
            self.fp.write('{"movies":['.encode())

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

        if self.crawler.settings['FILTER_TAGS']:
            item['tags'] = self.clean_tags(item['tags'], self.tagaliases)

        if 'length' in item and 'duration' not in item:
            item['duration'] = None
            if item['length']:
                length = int(item['length'])
                if length < 450:
                    length = length * 60
                item['length'] = str(length)
                item['duration'] = str(length)

        if "markers" not in item:
            item['markers'] = []

        payload = {
            'title': item['title'],
            'description': item['description'],
            'site': item['site'],
            'date': item['date'],
            'front': item['front'],
            'front_blob': item['front_blob'],
            'back': item['back'],
            'back_blob': item['back_blob'],
            'performers': item['performers'],
            'tags': item['tags'],
            'url': item['url'],
            'external_id': str(item['id']),
            'trailer': item['trailer'],
            'markers': item['markers'],
            'studio': item['studio'],
            'director': item['director'],
            'format': item['format'],
            'length': item['length'],
            'duration': item['duration'],
            'year': item['year'],
            'rating': item['rating'],
            'sku': item['sku'],
            'upc': item['upc'],
            'store': item['store'],
            'force_update': self.crawler.settings.getbool('FORCE_UPDATE'),
        }

        # Post the scene to the API - requires auth with permissions
        disp_result = ""
        if self.crawler.settings['TPDB_API_KEY'] and not spider.settings.get('local'):
            headers = {
                'Authorization': f'Bearer {self.crawler.settings["TPDB_API_KEY"]}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'tpdb-scraper/1.0.0'
            }

            response = Http.post('https://api.metadataapi.net/movies', json=payload, headers=headers, verify=False, timeout=2)
            if response:
                if response.ok:
                    disp_result = f'{disp_result} Submitted OK'
                else:
                    disp_result = f'{disp_result} Submission Error: Code #{response.status_code}'
            else:
                disp_result = disp_result + 'Submission Error: No Response Code'
                if response:
                    logging.info(response.content)
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

        if spider.settings.get('localdump'):
            # Toss to local TPDB Instance
            headers = {
                'Authorization': f'Bearer {self.crawler.settings["TPDB_TEST_API_KEY"]}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'tpdb-scraper/1.0.0'
            }
            response = Http.post('http://api.tpdb.test/movies', json=payload, headers=headers)
            if response:
                if response.ok:
                    disp_result = disp_result + '\tSubmitted to Local OK'
                else:
                    disp_result = disp_result + f'\tSubmission to Local Error: Code #{response.status_code}'
            else:
                disp_result = disp_result + '\tSubmission to Local Error: No Response Code'
                if response:
                    logging.info(response.content)
            # #############################

        if (spider.settings.getbool('display') or self.crawler.settings['DISPLAY_ITEMS']) and spider.settings.get('LOG_LEVEL') == 'INFO':
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

            logging.info(f"Item: {item['title'][0:50]}" + " " * title_length + f"{item['site'][0:15]}" + " " * site_length + f"\t{str(item['id'])[0:15]}\t{disp_date}\t{item['url']}\t{disp_result}")

        if spider.settings.getbool('export') or self.crawler.settings['EXPORT_ITEMS']:
            item2 = item.copy()
            if not spider.settings.get('showblob'):
                if 'front_blob' in item2:
                    item2.pop('front_blob', None)
                if 'back_blob' in item2:
                    item2.pop('back_blob', None)
            self.exporter.export_item(item2)

        return item

    def clean_tags(self, tags, aliaslist):
        tags2 = []
        if tags:
            for tag in tags:
                pointer = 0
                for alias in aliaslist:
                    if not pointer and tag.lower().strip() == alias['alias'].lower().strip():
                        tags2.append(alias['tag'])
                        pointer = 1
                        break
                if not pointer:
                    tags2.append(tag.rstrip(".").rstrip(",").strip())

        tags2 = [i for n, i in enumerate(tags2) if i not in tags2[:n]]
        return tags2

    def close_spider(self, spider):
        if spider.settings.getbool('export') or self.crawler.settings['EXPORT_ITEMS']:
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
            filename = Path(path, f'{crawler.spidercls.name}_{time.strftime("%Y%m%d-%H%M")}-performers.json')

        if crawler.settings.getbool('export') or self.crawler.settings['EXPORT_ITEMS']:
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

        if 'fakeboobs' in item and item['fakeboobs']:
            if item['fakeboobs'].lower() == 'yes':
                item['fakeboobs'] = True
            elif item['fakeboobs'].lower() == 'no':
                item['fakeboobs'] = False
            else:
                item['fakeboobs'] = None

        payload = {
            'name': item['name'],
            'site': item['network'],
            'network': item['network'],
            'url': item['url'],
            'bio': item['bio'],
            'image': item['image'],
            'image_blob': item['image_blob'],
            'extra': {
                'gender': item['gender'],
                'birthday': item['birthday'],
                'astrology': item['astrology'],
                'birthplace': item['birthplace'],
                'ethnicity': item['ethnicity'],
                'nationality': item['nationality'],
                'haircolor': item['haircolor'],
                'eyecolor': item['eyecolor'],
                'weight': item['weight'],
                'height': item['height'],
                'measurements': item['measurements'],
                'tattoos': item['tattoos'],
                'piercings': item['piercings'],
                'cupsize': item['cupsize'],
                'fakeboobs': item['fakeboobs']
            }
        }

        # Post the scene to the API - requires auth with permissions
        disp_result = ""
        if self.crawler.settings['TPDB_API_KEY'] and not spider.settings.get('local'):
            headers = {
                'Authorization': f'Bearer {self.crawler.settings["TPDB_API_KEY"]}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'tpdb-scraper/1.0.0'
            }

            response = Http.post('https://api.metadataapi.net/performer_sites', json=payload, headers=headers, verify=False, timeout=2)
            if response:
                if response.ok:
                    disp_result = 'Submitted OK'
                else:
                    disp_result = 'Submission Error: Code #' + str(response.status_code)
            else:
                disp_result = 'Submission Error: No Response Code'
                if response:
                    logging.info(response.content)

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

        if spider.settings.get('localdump'):
            # Toss to local TPDB Instance
            headers = {
                'Authorization': f'Bearer {self.crawler.settings["TPDB_TEST_API_KEY"]}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'tpdb-scraper/1.0.0'
            }

            response = Http.post('http://api.tpdb.test/performer_sites', json=payload, headers=headers, verify=False)
            if response:
                if response.ok:
                    disp_result = disp_result + '\tSubmitted to Local OK'
                else:
                    disp_result = disp_result + f'\tSubmission to Local Error: Code #{response.status_code}'
            else:
                disp_result = disp_result + '\tSubmission to Local Error: No Response Code'
                if response:
                    logging.info(response.content)
            # ##############################

        if (spider.settings.getbool('display') or self.crawler.settings['DISPLAY_ITEMS']) and spider.settings.get('LOG_LEVEL') == 'INFO':
            name_length = 50 - len(payload['name'])
            if name_length < 1:
                name_length = 1

            logging.info(f"Performer: {payload['name']}" + " " * name_length + f"{payload['site']}\t{payload['url']}\t{disp_result}")

        if spider.settings.getbool('export') or self.crawler.settings['EXPORT_ITEMS']:
            item2 = payload.copy()
            if not spider.settings.get('showblob'):
                if "image_blob" in item2:
                    item2.pop('image_blob', None)
            self.exporter.export_item(item2)

        return item

    def close_spider(self, spider):
        if spider.settings.getbool('export') or self.crawler.settings['EXPORT_ITEMS']:
            self.fp.write(']}'.encode())
            self.fp.close()

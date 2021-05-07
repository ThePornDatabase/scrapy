import dateparser
import scrapy
from scrapy.utils.response import open_in_browser

from tpdb.items import SceneItem
from tpdb.scrapy_dpath import ScrapyDPath
import tldextract
import re
from urllib.parse import urlparse


class BaseSceneScraper(scrapy.Spider):
    limit_pages = 1
    force = False
    debug = False
    max_pages = 100
    cookies = {}
    headers = {}
    page = 1

    custom_settings = {
        'ITEM_PIPELINES': {
            'tpdb.pipelines.TpdbApiScenePipeline': 400,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'tpdb.middlewares.TpdbSceneDownloaderMiddleware': 543,
        }
    }

    def __init__(self, *args, **kwargs):
        super(BaseSceneScraper, self).__init__(*args, **kwargs)

        self.force = bool(self.force)
        self.debug = bool(self.debug)
        self.page = int(self.page)

        if self.limit_pages is None:
            self.limit_pages = 1
        else:
            if self.limit_pages == 'all':
                self.limit_pages = 9999
            self.limit_pages = int(self.limit_pages)

    def start_requests(self):
        if not hasattr(self, 'start_urls'):
            raise AttributeError('start_urls missing')

        if not self.start_urls:
            raise AttributeError('start_urls selector missing')

        for link in self.start_urls:
            yield scrapy.Request(url=self.get_next_page_url(link, self.page),
                                 callback=self.parse,
                                 meta={'page': self.page},
                                 headers=self.headers,
                                 cookies=self.cookies)

    def parse(self, response, **kwargs):
        if response.status == 200:
            scenes = self.get_scenes(response)
            count = 0
            for scene in scenes:
                count += 1
                yield scene

            if count:
                if 'page' in response.meta and response.meta['page'] < self.limit_pages:
                    next_page = response.meta['page'] + 1
                    print('NEXT PAGE: ' + str(next_page))
                    yield scrapy.Request(url=self.get_next_page_url(response.url, next_page),
                                         callback=self.parse,
                                         meta={'page': next_page},
                                         headers=self.headers,
                                         cookies=self.cookies)

    def get_scenes(self, response):
        return []

    def get_selector_map(self, attr=None):
        if hasattr(self, 'selector_map'):
            if attr is None:
                return self.selector_map
            if attr not in self.selector_map:
                raise AttributeError(attr + ' missing from selector map')
            return self.selector_map[attr]
        raise NotImplementedError('selector map missing')

    def parse_scene(self, response):
        item = SceneItem()

        if 'title' in response.meta and response.meta['title']:
            item['title'] = response.meta['title']
        else:
            item['title'] = self.get_title(response)

        if 'description' in response.meta:
            item['description'] = response.meta['description']
        else:
            item['description'] = self.get_description(response)

        if 'site' in response.meta:
            item['site'] = response.meta['site']
        else:
            item['site'] = self.get_site(response)

        if 'date' in response.meta:
            item['date'] = response.meta['date']
        else:
            item['date'] = self.get_date(response)

        if 'image' in response.meta:
            item['image'] = response.meta['image']
        else:
            item['image'] = self.get_image(response)

        if 'performers' in response.meta:
            item['performers'] = response.meta['performers']
        else:
            item['performers'] = self.get_performers(response)

        if 'tags' in response.meta:
            item['tags'] = response.meta['tags']
        else:
            item['tags'] = self.get_tags(response)

        if 'id' in response.meta:
            item['id'] = response.meta['id']
        else:
            item['id'] = self.get_id(response)

        if 'trailer' in response.meta:
            item['trailer'] = response.meta['trailer']
        else:
            item['trailer'] = self.get_trailer(response)

        item['url'] = self.get_url(response)

        if hasattr(self, 'parent'):
            item['parent'] = self.parent
        else:
            item['parent'] = self.get_parent(response)

        if hasattr(self, 'network'):
            item['network'] = self.network
        else:
            item['network'] = self.get_network(response)

        if self.debug:
            print(item)
        else:
            return item

    def get_title(self, response):
        return self.process_xpath(
            response, self.get_selector_map('title')).get().strip()

    def get_description(self, response):
        if 'description' not in self.get_selector_map():
            return ''

        description = self.process_xpath(
            response, self.get_selector_map('description')).get()

        if description is not None:
            return description.replace('Description:', '').strip()
        return ""

    def get_site(self, response):
        return tldextract.extract(response.url).domain

    def get_parent(self, response):
        return tldextract.extract(response.url).domain

    def get_network(self, response):
        return tldextract.extract(response.url).domain

    def get_date(self, response):
        date = self.process_xpath(response, self.get_selector_map('date')).get()
        date.replace('Released:', '').replace('Added:', '').strip()
        return dateparser.parse(date.strip()).isoformat()

    def get_image(self, response):
        image = self.process_xpath(
            response, self.get_selector_map('image')).get()
        return self.format_link(response, image)

    def get_performers(self, response):
        performers = self.process_xpath(
            response, self.get_selector_map('performers')).getall()
        return list(map(lambda x: x.strip(), performers))

    def get_tags(self, response):
        if self.get_selector_map('tags'):
            tags = self.process_xpath(
                response, self.get_selector_map('tags')).getall()
            return list(map(lambda x: x.strip(), tags))
        return []

    def get_url(self, response):
        return response.url

    def get_id(self, response):
        search = re.search(self.get_selector_map(
            'external_id'), response.url, re.IGNORECASE)
        return search.group(1)

    def get_trailer(self, response):
        if 'trailer' in self.get_selector_map() and self.get_selector_map('trailer'):
            return self.process_xpath(
                response, self.get_selector_map('trailer')).get()
        return ''

    def process_xpath(self, response, selector):
        if selector.startswith('//'):
            return response.xpath(selector)
        elif selector.startswith('/'):
            return ScrapyDPath(response, selector)
        else:
            return response.css(selector)

    def format_link(self, response, link):
        return self.format_url(response.url, link)

    def format_url(self, base, path):
        if path.startswith('http'):
            return path

        new_url = urlparse(path)
        url = urlparse(base)
        url = url._replace(path=new_url.path, query=new_url.query)
        return url.geturl()

    def get_next_page_url(self, base, page):
        return self.format_url(
            base, self.get_selector_map('pagination') % page)

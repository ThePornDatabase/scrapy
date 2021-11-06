import re
from urllib.parse import urlparse

import dateparser
import scrapy
import tldextract
import string
import html
import requests
import base64

from tpdb.items import SceneItem


class BaseSceneScraper(scrapy.Spider):
    limit_pages = 1
    force = False
    debug = False
    max_pages = 100
    cookies = {}
    headers = {}
    page = 1

    custom_tpdb_settings = {
        'ITEM_PIPELINES': {
            'tpdb.pipelines.TpdbApiScenePipeline': 400,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'tpdb.middlewares.TpdbSceneDownloaderMiddleware': 543,
        }
    }

    custom_scraper_settings = {}

    regex = {
        'external_id': None,
        're_title': None,
        're_description': None,
        're_date': None,
        're_image': None,
        're_trailer': None,
    }

    def __init__(self, *args, **kwargs):
        super(BaseSceneScraper, self).__init__(*args, **kwargs)

        for name in self.get_selector_map():
            if (name == 'external_id' or name.startswith('re_')) and name in self.get_selector_map() and self.get_selector_map()[name]:
                self.regex[name] = re.compile(self.get_selector_map(name), re.IGNORECASE)

        self.force = bool(self.force)
        self.debug = bool(self.debug)
        self.page = int(self.page)

        if self.limit_pages is None:
            self.limit_pages = 1
        else:
            if self.limit_pages == 'all':
                self.limit_pages = 9999
            self.limit_pages = int(self.limit_pages)

    @classmethod
    def update_settings(self, settings):
        self.custom_tpdb_settings.update(self.custom_scraper_settings)
        settings.update(self.custom_tpdb_settings)
        super(BaseSceneScraper, self).update_settings(settings)

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
        scenes = self.get_scenes(response)
        count = 0
        for scene in scenes:
            count += 1
            yield scene

        if count:
            if 'page' in response.meta and response.meta['page'] < self.limit_pages:
                meta = response.meta
                meta['page'] = meta['page'] + 1
                print('NEXT PAGE: ' + str(meta['page']))
                yield scrapy.Request(url=self.get_next_page_url(response.url, meta['page']),
                                     callback=self.parse,
                                     meta=meta,
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

        if hasattr(self, 'site'):
            item['site'] = self.site
        elif 'site' in response.meta:
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

        if 'image_blob' in response.meta:
            item['image_blob'] = response.meta['image_blob']
        else:
            item['image_blob'] = self.get_image_blob(response)

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

        if hasattr(self, 'network'):
            item['network'] = self.network
        elif 'network' in response.meta:
            item['network'] = response.meta['network']
        else:
            item['network'] = self.get_network(response)

        if hasattr(self, 'parent'):
            item['parent'] = self.parent
        elif 'parent' in response.meta:
            item['parent'] = response.meta['parent']
        else:
            item['parent'] = self.get_parent(response)

        if self.debug:
            print(item)
        else:
            yield item

    def get_title(self, response):
        title = self.process_xpath(response, self.get_selector_map('title'))
        if title:
            title = self.get_from_regex(title.get(), 're_title')

            if title:
                return string.capwords(html.unescape(title.strip()))

        return None

    def get_description(self, response):
        if 'description' not in self.get_selector_map():
            return ''

        description = self.process_xpath(response, self.get_selector_map('description'))
        if description:
            description = self.get_from_regex(description.get(), 're_description')

            if description:
                description = description.replace('Description:', '')

                return html.unescape(description.strip())

        return ''

    def get_site(self, response):
        return tldextract.extract(response.url).domain

    def get_network(self, response):
        return tldextract.extract(response.url).domain

    def get_parent(self, response):
        return tldextract.extract(response.url).domain

    def get_date(self, response):
        date = self.process_xpath(response, self.get_selector_map('date'))
        if date:
            date = self.get_from_regex(date.get(), 're_date')

            if date:
                date = date.replace('Released:', '').replace('Added:', '').strip()
                date_formats = self.get_selector_map('date_formats') if 'date_formats' in self.get_selector_map() else None

                return dateparser.parse(date, date_formats=date_formats).isoformat()

        return None

    def get_image(self, response):
        image = self.process_xpath(response, self.get_selector_map('image'))
        if image:
            image = self.get_from_regex(image.get(), 're_image')

            if image:
                image = self.format_link(response, image)
                return image.replace(" ", "%20")

        return None

    def get_image_blob(self, response):
        if self.get_selector_map('image_blob'):
            image = self.process_xpath(response, self.get_selector_map('image_blob'))
            if image:
                image = self.get_from_regex(image.get(), 're_image_blob')

                if image:
                    image = self.format_link(response, image)
                    return base64.b64encode(requests.get(image).content).decode('utf-8')
        return None

    def get_performers(self, response):
        performers = self.process_xpath(response, self.get_selector_map('performers'))
        if performers:
            return list(map(lambda x: x.strip(), performers.getall()))

        return []

    def get_tags(self, response):
        if self.get_selector_map('tags'):
            tags = self.process_xpath(response, self.get_selector_map('tags'))
            if tags:
                return list(map(lambda x: x.strip().title(), tags.getall()))

        return []

    def get_url(self, response):
        return response.url

    def get_id(self, response):
        if 'external_id' in self.regex and self.regex['external_id']:
            search = self.regex['external_id'].search(response.url)
            if search:
                return search.group(1)

        return None

    def get_trailer(self, response):
        if 'trailer' in self.get_selector_map() and self.get_selector_map('trailer'):
            trailer = self.process_xpath(response, self.get_selector_map('trailer'))
            if trailer:
                trailer = self.get_from_regex(trailer.get(), 're_trailer')
                trailer = self.format_link(response, trailer)
                return trailer.replace(" ", "%20")

        return ''

    def process_xpath(self, response, selector):
        if selector.startswith('/') or selector.startswith('./'):
            return response.xpath(selector)
        else:
            return response.css(selector)

    def format_link(self, response, link):
        return self.format_url(response.url, link)

    def format_url(self, base, path):
        if path.startswith('http'):
            return path

        if path.startswith('//'):
            return 'https:' + path

        new_url = urlparse(path)
        url = urlparse(base)
        url = url._replace(path=new_url.path, query=new_url.query)

        return url.geturl()

    def get_next_page_url(self, base, page):
        return self.format_url(base, self.get_selector_map('pagination') % page)

    def get_from_regex(self, text, re_name, group=1):
        if re_name in self.regex and self.regex[re_name]:
            r = self.regex[re_name].search(text)
            if r:
                return r.group(group)
            else:
                return None

        return text

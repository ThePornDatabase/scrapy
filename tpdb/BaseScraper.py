import sys
import re
import base64
import html
import string
from abc import ABC
from urllib.parse import urlparse

import dateparser
import scrapy
import tldextract

from tpdb.helpers.http import Http


class BaseScraper(scrapy.Spider, ABC):
    limit_pages = 1
    force = False
    debug = False
    days = 99999
    max_pages = 100
    cookies = {}
    headers = {}
    page = 1

    custom_tpdb_settings = {}
    custom_scraper_settings = {}
    selector_map = {}
    regex = {}

    title_trash = []
    description_trash = ['Description:']
    date_trash = ['Released:', 'Added:', 'Published:']

    def __init__(self, *args, **kwargs):
        super(BaseScraper, self).__init__(*args, **kwargs)

        for name in self.get_selector_map():
            if (name == 'external_id' or name.startswith('re_')) and name in self.get_selector_map() and self.get_selector_map()[name]:
                regexp, group, mod = self.get_regex(self.get_selector_map(name))
                self.regex[name] = (re.compile(regexp, mod), group)

        self.days = int(self.days)
        self.force = bool(self.force)
        self.debug = bool(self.debug)
        self.page = int(self.page)

        if self.limit_pages is None:
            self.limit_pages = 1
        else:
            if self.limit_pages == 'all':
                self.limit_pages = sys.maxsize
            self.limit_pages = int(self.limit_pages)

    @classmethod
    def update_settings(cls, settings):
        cls.custom_tpdb_settings.update(cls.custom_scraper_settings)
        settings.update(cls.custom_tpdb_settings)
        cls.headers['User-Agent'] = settings['USER_AGENT']
        super(BaseScraper, cls).update_settings(settings)

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

    def get_selector_map(self, attr=None):
        if hasattr(self, 'selector_map'):
            if attr is None:
                return self.selector_map
            if attr not in self.selector_map:
                raise AttributeError(f'{attr} missing from selector map')
            return self.selector_map[attr]
        raise NotImplementedError('selector map missing')

    def get_image(self, response):
        if 'image' not in self.get_selector_map():
            return ''

        if self.get_selector_map('image'):
            image = self.process_xpath(response, self.get_selector_map('image'))
            if image:
                image = self.get_from_regex(image.get(), 're_image')
                if image:
                    image = self.format_link(response, image)
                    return image.strip().replace(' ', '%20')

        return None

    def get_image_blob(self, response):
        if 'image_blob' not in self.get_selector_map():
            return None

        if self.get_selector_map('image_blob'):
            image = self.get_image(response)
            if image:
                image = self.format_link(response, image)
                req = Http.get(image, headers=self.headers, cookies=self.cookies)
                if req and req.ok:
                    return base64.b64encode(req.content).decode('utf-8')

        return None

    def get_image_blob_from_link(self, image):
        if image:
            req = Http.get(image, headers=self.headers, cookies=self.cookies)
            if req and req.ok:
                return base64.b64encode(req.content).decode('utf-8')
        return None

    def get_url(self, response):
        return response.url

    def get_id(self, response):
        return self.get_from_regex(response.url, 'external_id')

    def get_site(self, response):
        return tldextract.extract(response.url).domain

    def get_network(self, response):
        return tldextract.extract(response.url).domain

    def get_parent(self, response):
        return tldextract.extract(response.url).domain

    @staticmethod
    def process_xpath(response, selector):
        if selector.startswith('//') or selector.startswith('./'):
            return response.xpath(selector)

        if selector.startswith('/'):
            return response.dpath(selector)

        return response.css(selector)

    def format_link(self, response, link):
        return self.format_url(response.url, link)

    @staticmethod
    def format_url(base, path):
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

    def get_from_regex(self, text, re_name):
        if re_name in self.regex and self.regex[re_name]:
            regexp, group, mod = self.get_regex(self.regex[re_name])

            r = regexp.search(text)
            if r:
                return r.group(group)
            return None

        return text

    @staticmethod
    def get_regex(regexp, group=1, mod=re.IGNORECASE):
        if isinstance(regexp, tuple):
            mod = regexp[2] if len(regexp) > 2 else mod
            group = regexp[1] if len(regexp) > 1 else group
            regexp = regexp[0]

        return regexp, group, mod

    @staticmethod
    def cleanup_text(text, trash_words=None):
        if trash_words is None:
            trash_words = []

        text = html.unescape(text)
        for trash in trash_words:
            text = text.replace(trash, '')

        return text.strip()

    def cleanup_title(self, title):
        return string.capwords(self.cleanup_text(title, self.title_trash))

    def cleanup_description(self, description):
        return self.cleanup_text(description, self.description_trash)

    def cleanup_date(self, date):
        return self.cleanup_text(date, self.date_trash)

    def parse_date(self, date, date_formats=None):
        date = self.cleanup_date(date)
        settings = {'TIMEZONE': 'UTC'}

        return dateparser.parse(date, date_formats=date_formats, settings=settings)

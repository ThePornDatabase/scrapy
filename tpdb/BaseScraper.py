import sys
from datetime import date, timedelta
import re
from PIL import Image
import base64
from io import BytesIO
import html
import logging
import string
from abc import ABC
from urllib.parse import urlparse, unquote

import dateparser
import scrapy
import tldextract

from furl import furl
from tpdb.helpers.http import Http
from scrapy.utils.project import get_project_settings


class BaseScraper(scrapy.Spider, ABC):
    limit_pages = 1
    force = False
    debug = False
    days = 9999
    max_pages = 100
    cookies = {}
    headers = {}
    page = 1

    custom_tpdb_settings = {}
    custom_scraper_settings = {}
    selector_map = {}
    regex = {}
    proxy_address = None

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
        if self.days < 9999:
            logging.info(f"Days to retrieve: {self.days}")
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
        if settings['DAYS']:
            cls.days = settings['DAYS']
        super(BaseScraper, cls).update_settings(settings)

    def start_requests(self):
        settings = get_project_settings()

        if not hasattr(self, 'start_urls'):
            raise AttributeError('start_urls missing')

        if not self.start_urls:
            raise AttributeError('start_urls selector missing')

        meta = {}
        meta['page'] = self.page
        if 'USE_PROXY' in self.settings.attributes.keys():
            use_proxy = self.settings.get('USE_PROXY')
        elif 'USE_PROXY' in settings.attributes.keys():
            use_proxy = settings.get('USE_PROXY')
        else:
            use_proxy = None

        if use_proxy:
            print(f"Using Settings Defined Proxy: True ({settings.get('PROXY_ADDRESS')})")
        else:
            if self.proxy_address:
                meta['proxy'] = self.proxy_address
                print(f"Using Scraper Defined Proxy: True ({meta['proxy']})")
            else:
                print("Using Proxy: False")

        for link in self.start_urls:
            yield scrapy.Request(url=self.get_next_page_url(link, self.page), callback=self.parse, meta=meta, headers=self.headers, cookies=self.cookies)

    def get_selector_map(self, attr=None):
        if hasattr(self, 'selector_map'):
            if attr is None:
                return self.selector_map
            if attr not in self.selector_map:
                raise AttributeError(f'{attr} missing from selector map')
            return self.selector_map[attr]
        raise NotImplementedError('selector map missing')

    def get_image(self, response, path=None):
        force_update = self.settings.get('force_update')
        if force_update:
            force_update = True
        force_fields = self.settings.get('force_fields')
        if force_fields:
            force_fields = force_fields.split(",")

        if not force_update or (force_update and "image" in force_fields):
            if 'image' in self.get_selector_map():
                image = self.get_element(response, 'image', 're_image')
                if isinstance(image, list):
                    image = image[0]
                if path:
                    return self.format_url(path, image)
                else:
                    return self.format_link(response, image)
            return ''

    def get_back_image(self, response):
        if 'back' in self.get_selector_map():
            image = self.get_element(response, 'back', 're_back')
            if isinstance(image, list):
                image = image[0]
            return self.format_link(response, image)
        return ''

    def get_image_blob(self, response):
        if 'image_blob' not in self.get_selector_map():
            image = self.get_image(response)
            return self.get_image_blob_from_link(image)
        return None

    def get_image_back_blob(self, response):
        if 'image_blob' not in self.get_selector_map():
            image = self.get_back_image(response)
            return self.get_image_blob_from_link(image)
        return None

    def get_image_from_link(self, image):
        if image:
            req = Http.get(image, headers=self.headers, cookies=self.cookies)
            if req and req.ok:
                return req.content
        return None

    def get_image_blob_from_link(self, image):
        force_update = self.settings.get('force_update')
        if force_update:
            force_update = True
        force_fields = self.settings.get('force_fields')
        if force_fields:
            force_fields = force_fields.split(",")

        if (not force_update or (force_update and "image" in force_fields)) and image:
            data = self.get_image_from_link(image)
            if data:
                try:
                    img = BytesIO(data)
                    img = Image.open(img)
                    img = img.convert('RGB')
                    width, height = img.size
                    if height > 1080 or width > 1920:
                        img.thumbnail((1920, 1080))
                    buffer = BytesIO()
                    img.save(buffer, format="JPEG")
                    data = buffer.getvalue()
                except Exception as ex:
                    print(f"Could not decode image for evaluation: '{image}'.  Error: ", ex)
                return base64.b64encode(data).decode('utf-8')
        return None

    @staticmethod
    def duration_to_seconds(time_text):
        duration = ''
        if ":" in time_text:
            time_text = time_text.split(":")
            time_text = [i for i in time_text if i]
            if len(time_text) == 3:
                duration = str(int(time_text[0]) * 3600 + int(time_text[1]) * 60 + int(time_text[2]))
            elif len(time_text) == 2:
                duration = str(int(time_text[0]) * 60 + int(time_text[1]))
            elif len(time_text) == 1:
                duration = time_text[0]
        elif re.search(r'(\d{1,2})M(\d{1,2})S', time_text):
            if "H" in time_text:
                duration = re.search(r'(\d{1,2})H(\d{1,2})M(\d{1,2})S', time_text)
                hours = int(duration.group(1)) * 3660
                minutes = int(duration.group(2)) * 60
                seconds = int(duration.group(3))
                duration = str(hours + minutes + seconds)
            else:
                duration = re.search(r'(\d{1,2})M(\d{1,2})S', time_text)
                minutes = int(duration.group(1)) * 60
                seconds = int(duration.group(2))
                duration = str(minutes + seconds)
        return duration

    def get_url(self, response):
        return self.prepare_url(response.url)

    def get_id(self, response):
        sceneid = self.get_from_regex(response.url, 'external_id')
        if "?nats" in sceneid:
            sceneid = re.search(r'(.*)\?nats', sceneid).group(1)
        return sceneid

    def get_site(self, response):
        return tldextract.extract(response.url).domain

    def get_network(self, response):
        return tldextract.extract(response.url).domain

    def get_parent(self, response):
        return tldextract.extract(response.url).domain

    def get_studio(self, response):
        if 'studio' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'studio', 're_studio')))
        return ''

    @staticmethod
    def process_xpath(response, selector: str):
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

        return BaseScraper.prepare_url(url.geturl())

    @staticmethod
    def prepare_url(url: str) -> str:
        return furl(unquote(url)).url

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

    def cleanup_date(self, item_date):
        return self.cleanup_text(item_date, self.date_trash)

    def parse_date(self, item_date, date_formats=None):
        item_date = self.cleanup_date(item_date)
        settings = {'TIMEZONE': 'UTC'}

        return dateparser.parse(item_date, date_formats=date_formats, settings=settings)

    def check_item(self, item, days=None):
        if 'date' not in item:
            return item
        if item['date']:
            if days:
                if days > 27375:
                    filter_date = '0000-00-00'
                else:
                    days = self.days
                    filter_date = date.today() - timedelta(days)
                    filter_date = filter_date.strftime('%Y-%m-%d')

                if self.debug:
                    if not item['date'] > filter_date:
                        item['filtered'] = 'Scene filtered due to date restraint'
                    print(item)
                else:
                    if filter_date:
                        if item['date'] > filter_date:
                            return item
                        return None
        return item

    def get_element(self, response, selector, regex=None):
        selector = self.get_selector_map(selector)
        if selector:
            element = self.process_xpath(response, selector)
            if element:
                if (len(element) > 1 or regex == "list") and "/script" not in selector:
                    element = list(map(lambda x: x.strip(), element.getall()))
                else:
                    if isinstance(element, list):
                        element = element.getall()
                        element = " ".join(element)
                    else:
                        element = element.get()
                    element = self.get_from_regex(element, regex)
                    if element:
                        element = element.strip()
                if element:
                    if isinstance(element, list):
                        element = [i for i in element if i]
                    return element
        return ''

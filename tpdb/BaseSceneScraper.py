from datetime import date, datetime, timedelta
import string
import scrapy

from tpdb.BaseScraper import BaseScraper
from tpdb.items import SceneItem


class BaseSceneScraper(BaseScraper):
    custom_tpdb_settings = {
        'ITEM_PIPELINES': {
            'tpdb.pipelines.TpdbApiScenePipeline': 400,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'tpdb.helpers.scrapy_dpath.DPathMiddleware': 542,
            'tpdb.middlewares.TpdbSceneDownloaderMiddleware': 543,
        }
    }

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

        if 'image' not in item or not item['image']:
            item['image'] = None

        if 'image_blob' in response.meta:
            item['image_blob'] = response.meta['image_blob']
        else:
            item['image_blob'] = self.get_image_blob(response)

        if ('image_blob' not in item or not item['image_blob']) and item['image']:
            item['image_blob'] = self.get_image_blob_from_link(item['image'])

        if 'image_blob' not in item:
            item['image_blob'] = None

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

        if self.days > 27375:
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
                    yield item
            else:
                yield item

    def get_title(self, response):
        title = self.process_xpath(response, self.get_selector_map('title'))
        if title:
            title = self.get_from_regex(title.get(), 're_title')

            if title:
                title = self.cleanup_title(title)
                return string.capwords(title)

        return None

    def get_description(self, response):
        if 'description' not in self.get_selector_map():
            return ''

        if self.get_selector_map('description'):
            description_xpath = self.process_xpath(response, self.get_selector_map('description'))
            if description_xpath:
                if len(description_xpath) > 1:
                    description = list(map(lambda x: x.strip(), description_xpath.getall()))
                    description = ' '.join(description)
                else:
                    description = description_xpath.get()

                description = self.get_from_regex(description, 're_description')
                if description:
                    return self.cleanup_description(description)

        return ''

    def get_date(self, response):
        if 'date' in self.get_selector_map():
            if self.get_selector_map('date'):
                date_xpath = self.process_xpath(response, self.get_selector_map('date'))
                if date_xpath:
                    date_xpath = self.get_from_regex(date_xpath.get().strip(), 're_date')
                    if date_xpath:
                        date_formats = self.get_selector_map('date_formats') if 'date_formats' in self.get_selector_map() else None
                        return self.parse_date(date_xpath, date_formats=date_formats).isoformat()

        return datetime.now().isoformat()

    def get_performers(self, response):
        if 'performers' in self.get_selector_map():
            if self.get_selector_map('performers'):
                performers = self.process_xpath(response, self.get_selector_map('performers'))
                if performers:
                    return list(map(lambda x: string.capwords(x.strip()), performers.getall()))

        return []

    def get_tags(self, response):
        if 'tags' not in self.get_selector_map():
            return []

        if self.get_selector_map('tags'):
            tags = self.process_xpath(response, self.get_selector_map('tags'))
            if tags:
                new_tags = []
                for tag in tags.getall():
                    if ',' in tag:
                        new_tags.extend(tag.split(','))
                    elif tag:
                        new_tags.append(tag)

                return list(map(lambda x: string.capwords(x.strip()), set(new_tags)))

        return []

    def get_trailer(self, response):
        if 'trailer' in self.get_selector_map():
            if self.get_selector_map('trailer'):
                trailer = self.process_xpath(response, self.get_selector_map('trailer'))
                if trailer:
                    trailer = self.get_from_regex(trailer.get(), 're_trailer')
                    if trailer:
                        trailer = self.format_link(response, trailer)
                        return trailer.strip().replace(' ', '%20')

        return ''

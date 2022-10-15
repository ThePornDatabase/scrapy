import re
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
            'tpdb.custommiddlewares.CustomProxyMiddleware': 350,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 400,
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

        if 'markers' in response.meta:
            item['markers'] = response.meta['markers']
        else:
            item['markers'] = self.get_markers(response)

        if 'id' in response.meta:
            item['id'] = response.meta['id']
        else:
            item['id'] = self.get_id(response)

        if 'trailer' in response.meta:
            item['trailer'] = response.meta['trailer']
        else:
            item['trailer'] = self.get_trailer(response)

        if 'duration' in response.meta:
            item['duration'] = response.meta['duration']
        else:
            item['duration'] = self.get_duration(response)

        if 'url' in response.meta:
            item['url'] = response.meta['url']
        else:
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

        # Movie Items

        if 'store' in response.meta:
            item['store'] = response.meta['store']
        else:
            item['store'] = self.get_store(response)

        if 'director' in response.meta:
            item['director'] = response.meta['director']
        else:
            item['director'] = self.get_director(response)

        if 'format' in response.meta:
            item['format'] = response.meta['format']
        else:
            item['format'] = self.get_format(response)

        if 'back' in response.meta:
            item['back'] = response.meta['back']
        else:
            item['back'] = self.get_back_image(response)

        if 'back' not in item or not item['back']:
            item['back'] = None
            item['back_blob'] = None
        else:
            if 'back_blob' in response.meta:
                item['back_blob'] = response.meta['back_blob']
            else:
                item['back_blob'] = self.get_image_back_blob(response)

            if ('back_blob' not in item or not item['back_blob']) and item['back']:
                item['back_blob'] = self.get_image_from_link(item['back'])

        if 'back_blob' not in item:
            item['back_blob'] = None

        if 'sku' in response.meta:
            item['sku'] = response.meta['sku']
        else:
            item['sku'] = self.get_sku(response)

        if hasattr(self, 'type'):
            item['type'] = self.type
        elif 'type' in response.meta:
            item['type'] = response.meta['type']
        elif 'type' in self.get_selector_map():
            item['type'] = self.get_selector_map('type')
        else:
            item['type'] = 'Scene'

        yield self.check_item(item, self.days)

    def get_date(self, response):
        if 'date' in self.get_selector_map():
            scenedate = self.get_element(response, 'date', 're_date')
            if scenedate:
                if isinstance(scenedate, list):
                    scenedate = scenedate[0]
                date_formats = self.get_selector_map('date_formats') if 'date_formats' in self.get_selector_map() else None
                return self.parse_date(self.cleanup_text(scenedate), date_formats=date_formats).isoformat()
        return self.parse_date('today').isoformat()

    def get_tags(self, response):
        if 'tags' in self.get_selector_map():
            tags = self.get_element(response, 'tags', "list")
            if tags and isinstance(tags, list):
                new_tags = []
                for tag in tags:
                    if ',' in tag:
                        new_tags.extend(tag.split(','))
                    elif tag:
                        new_tags.append(tag)
                return list(map(lambda x: string.capwords(x.strip()), new_tags))
        return []

    def get_performers(self, response):
        if 'performers' in self.get_selector_map():
            performers = self.get_element(response, 'performers', "list")
            if performers and isinstance(performers, list):
                return list(map(lambda x: string.capwords(x.strip()), performers))
        return []

    def get_description(self, response):
        if 'description' in self.get_selector_map():
            description = self.get_element(response, 'description', 're_description')
            if isinstance(description, list):
                description = ' '.join(description)
            if description:
                return self.cleanup_description(description)
        return ''

    def get_trailer(self, response):
        if 'trailer' in self.get_selector_map():
            trailer = self.get_element(response, 'trailer', 're_trailer')
            if trailer:
                return self.format_link(response, trailer).replace(' ', '%20')
        return ''

    def get_duration(self, response):
        if 'duration' in self.get_selector_map():
            duration = self.get_element(response, 'duration', 're_duration')
            if duration:
                if ":" in duration or re.search(r'(\d{1,2})M(\d{1,2})S', duration):
                    duration = self.duration_to_seconds(duration)
                return duration
        return ''

    def get_store(self, response):
        if 'store' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'store', 're_store')))
        return None

    def get_director(self, response):
        if 'director' in self.get_selector_map():
            director = self.get_element(response, 'director', 're_director')
            if director and isinstance(director, list):
                director = ", ".join(director)
            return string.capwords(self.cleanup_text(director))
        return None

    def get_format(self, response):
        if 'format' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'format', 're_format')))
        return None

    def get_sku(self, response):
        if 'sku' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'sku', 're_sku')))
        return None

    def get_markers(self, response):
        # Until there's a better feel for Markers, will need to be done in the scraper
        return []

    def get_title(self, response):
        if 'title' in self.get_selector_map():
            title = self.get_element(response, 'title', 're_title')
            if title:
                if isinstance(title, list):
                    title = title[0]
                return string.capwords(self.cleanup_text(title))
        return None

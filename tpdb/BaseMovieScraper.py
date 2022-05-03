from datetime import date, timedelta
import string
import scrapy

from tpdb.BaseScraper import BaseScraper
from tpdb.items import MovieItem


class BaseMovieScraper(BaseScraper):
    custom_tpdb_settings = {
        'ITEM_PIPELINES': {
            'tpdb.pipelines.TpdbApiMoviePipeline': 400,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'tpdb.custommiddlewares.CustomProxyMiddleware': 350,
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 400,
            'tpdb.helpers.scrapy_dpath.DPathMiddleware': 542,
            'tpdb.middlewares.TpdbMovieDownloaderMiddleware': 543,
        }
    }

    def parse(self, response, **kwargs):
        movies = self.get_movies(response)
        count = 0
        for movie in movies:
            count += 1
            yield movie

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

    def get_movies(self, response):
        return []

    def parse_movie(self, response):
        item = MovieItem()

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

        if hasattr(self, 'network'):
            item['network'] = self.network
        elif 'network' in response.meta:
            item['network'] = response.meta['network']
        else:
            item['network'] = item['site']

        if 'date' in response.meta:
            item['date'] = response.meta['date']
        else:
            item['date'] = self.get_date(response)

        if 'front' in response.meta:
            item['front'] = response.meta['front']
        else:
            item['front'] = self.get_image(response, 'front')

        if 'front' not in item or not item['front']:
            item['front'] = None

        if item['front']:
            item['front_blob'] = self.get_image_blob_from_link(item['front'])

        if 'back' in response.meta:
            item['back'] = response.meta['back']
        else:
            item['back'] = self.get_image(response, 'back')

        if 'back' not in item or not item['back']:
            item['back'] = None

        if item['back']:
            item['back_blob'] = self.get_image_blob_from_link(item['back'])

        if 'front_blob' not in item:
            item['front_blob'] = None

        if 'back_blob' not in item:
            item['back_blob'] = None

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

        if 'studio' in response.meta:
            item['studio'] = response.meta['studio']
        else:
            item['studio'] = self.get_studio(response)

        if 'director' in response.meta:
            item['director'] = response.meta['director']
        else:
            item['director'] = self.get_director(response)

        if 'format' in response.meta:
            item['format'] = response.meta['format']
        else:
            item['format'] = self.get_format(response)

        if 'length' in response.meta:
            item['length'] = response.meta['length']
        else:
            item['length'] = self.get_length(response)

        if 'year' in response.meta:
            item['year'] = response.meta['year']
        else:
            item['year'] = self.get_year(response)

        if 'rating' in response.meta:
            item['rating'] = response.meta['rating']
        else:
            item['rating'] = self.get_rating(response)

        if 'sku' in response.meta:
            item['sku'] = response.meta['sku']
        else:
            item['sku'] = self.get_sku(response)

        if 'upc' in response.meta:
            item['upc'] = response.meta['upc']
        else:
            item['upc'] = self.get_upc(response)

        item['url'] = self.get_url(response)

        yield self.check_item(item, self.days)

    def get_description(self, response):
        if 'description' in self.get_selector_map():
            description = self.get_element(response, 'description', 're_description')
            if isinstance(description, list):
                description = ' '.join(description)
            return self.cleanup_description(description)
        return ''

    def get_date(self, response):
        if 'date' in self.get_selector_map():
            scenedate = self.cleanup_text(self.get_element(response, 'date', 're_date'))
            if scenedate:
                date_formats = self.get_selector_map('date_formats') if 'date_formats' in self.get_selector_map() else None
                return self.parse_date(scenedate, date_formats=date_formats).isoformat()
        return self.parse_date('today').isoformat()

    def get_performers(self, response):
        if 'performers' in self.get_selector_map():
            performers = self.get_element(response, 'performers', "list")
            if performers and isinstance(performers, list):
                return list(map(lambda x: string.capwords(x.strip()), performers))
        return []

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

    def get_image(self, response, side):
        if side in self.get_selector_map():
            image = self.process_xpath(response, self.get_selector_map(side))
            if image:
                image_re = 're_' + side
                image = self.get_from_regex(image.get(), image_re)
                if image:
                    image = self.format_link(response, image)
                    return image.strip().replace(' ', '%20')
        return None

    def get_title(self, response):
        if 'title' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'title', 're_title')))
        return ''

    def get_trailer(self, response):
        if 'trailer' in self.get_selector_map():
            return self.format_link(response, self.get_element(response, 'trailer', 're_trailer')).replace(' ', '%20')
        return ''

    def get_studio(self, response):
        if 'studio' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'studio', 're_studio')))
        return ''

    def get_director(self, response):
        if 'director' in self.get_selector_map():
            director = self.get_element(response, 'director', 're_director')
            if director and isinstance(director, list):
                director = ", ".join(director)
            return string.capwords(self.cleanup_text(director))
        return ''

    def get_format(self, response):
        if 'format' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'format', 're_format')))
        return ''

    def get_length(self, response):
        if 'length' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'length', 're_length')))
        return ''

    def get_year(self, response):
        if 'year' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'year', 're_year')))
        return ''

    def get_rating(self, response):
        if 'rating' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'rating', 're_rating')))
        return ''

    def get_sku(self, response):
        if 'sku' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'sku', 're_sku')))
        return ''

    def get_upc(self, response):
        if 'upc' in self.get_selector_map():
            return string.capwords(self.cleanup_text(self.get_element(response, 'upc', 're_upc')))
        return ''

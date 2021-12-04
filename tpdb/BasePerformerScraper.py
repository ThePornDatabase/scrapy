import scrapy

from tpdb.BaseScraper import BaseScraper
from tpdb.items import PerformerItem


class BasePerformerScraper(BaseScraper):
    custom_settings = {
        'ITEM_PIPELINES': {
            'tpdb.pipelines.TpdbApiPerformerPipeline': 400,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'tpdb.middlewares.TpdbPerformerDownloaderMiddleware': 543,
        }
    }

    def parse(self, response, **kwargs):
        performers = self.get_performers(response)
        count = 0
        for performer in performers:
            count += 1
            yield performer

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

    def get_performers(self, response):
        return []

    def parse_performer(self, response):
        item = PerformerItem()

        if 'name' in response.meta and response.meta['name']:
            item['name'] = response.meta['name']
        else:
            item['name'] = self.get_name(response)

        if 'image' in response.meta and response.meta['image']:
            item['image'] = response.meta['image']
        else:
            item['image'] = self.get_image(response)

        if 'image' not in item or not item['image']:
            item['image'] = None

        if 'image_blob' in response.meta:
            item['image_blob'] = response.meta['image_blob']
        else:
            item['image_blob'] = self.get_image_blob(response)

        if 'image_blob' not in item or not item['image_blob']:
            item['image_blob'] = None

        if 'bio' in response.meta and response.meta['bio']:
            item['bio'] = response.meta['bio']
        else:
            item['bio'] = self.get_bio(response)

        if 'gender' in response.meta and response.meta['gender']:
            item['gender'] = response.meta['gender']
        else:
            item['gender'] = self.get_gender(response)

        if 'birthday' in response.meta and response.meta['birthday']:
            item['birthday'] = response.meta['birthday']
        else:
            item['birthday'] = self.get_birthday(response)

        if 'astrology' in response.meta and response.meta['astrology']:
            item['astrology'] = response.meta['astrology']
        else:
            item['astrology'] = self.get_astrology(response)

        if 'birthplace' in response.meta and response.meta['birthplace']:
            item['birthplace'] = response.meta['birthplace']
        else:
            item['birthplace'] = self.get_birthplace(response)

        if 'ethnicity' in response.meta and response.meta['ethnicity']:
            item['ethnicity'] = response.meta['ethnicity']
        else:
            item['ethnicity'] = self.get_ethnicity(response)

        if 'nationality' in response.meta and response.meta['nationality']:
            item['nationality'] = response.meta['nationality']
        else:
            item['nationality'] = self.get_nationality(response)

        if 'eyecolor' in response.meta and response.meta['eyecolor']:
            item['eyecolor'] = response.meta['eyecolor']
        else:
            item['eyecolor'] = self.get_eyecolor(response)

        if 'haircolor' in response.meta and response.meta['haircolor']:
            item['haircolor'] = response.meta['haircolor']
        else:
            item['haircolor'] = self.get_haircolor(response)

        if 'height' in response.meta and response.meta['height']:
            item['height'] = response.meta['height']
        else:
            item['height'] = self.get_height(response)

        if 'weight' in response.meta and response.meta['weight']:
            item['weight'] = response.meta['weight']
        else:
            item['weight'] = self.get_weight(response)

        if 'measurements' in response.meta and response.meta['measurements']:
            item['measurements'] = response.meta['measurements']
        else:
            item['measurements'] = self.get_measurements(response)

        if 'tattoos' in response.meta and response.meta['tattoos']:
            item['tattoos'] = response.meta['tattoos']
        else:
            item['tattoos'] = self.get_tattoos(response)

        if 'piercings' in response.meta and response.meta['piercings']:
            item['piercings'] = response.meta['piercings']
        else:
            item['piercings'] = self.get_piercings(response)

        if 'cupsize' in response.meta and response.meta['cupsize']:
            item['cupsize'] = response.meta['cupsize']
        else:
            item['cupsize'] = self.get_cupsize(response)

        if 'fakeboobs' in response.meta and response.meta['fakeboobs']:
            item['fakeboobs'] = response.meta['fakeboobs']
        else:
            item['fakeboobs'] = self.get_fakeboobs(response)

        item['url'] = self.get_url(response)

        if hasattr(self, 'network'):
            item['network'] = self.network
        elif 'network' in response.meta:
            item['network'] = response.meta['network']
        else:
            item['network'] = self.get_network(response)

        if self.debug:
            print(item)
        else:
            yield item

    def get_name(self, response):
        name = self.process_xpath(response, self.get_selector_map('name'))
        if name:
            name = self.get_from_regex(name.get(), 're_name')
            if name:
                return self.cleanup_text(name).title()

        return None

    def get_bio(self, response):
        if 'bio' not in self.get_selector_map():
            return ''

        bio = self.process_xpath(response, self.get_selector_map('bio'))
        if bio:
            bio = self.get_from_regex(bio.get(), 're_bio')
            if bio:
                return self.cleanup_text(bio)

        return ''

    def get_gender(self, response):
        if 'gender' in self.selector_map:
            gender = self.process_xpath(response, self.get_selector_map('gender')).get()
            if gender:
                return gender.strip()

        return ''

    def get_birthday(self, response):
        if 'birthday' in self.selector_map:
            birthday = self.process_xpath(response, self.get_selector_map('birthday')).get()
            if birthday:
                return birthday.strip()

        return ''

    def get_astrology(self, response):
        if 'astrology' in self.selector_map:
            astrology = self.process_xpath(response, self.get_selector_map('astrology')).get()
            if astrology:
                return astrology.strip()

        return ''

    def get_birthplace(self, response):
        if 'birthplace' in self.selector_map:
            birthplace = self.process_xpath(response, self.get_selector_map('birthplace')).get()
            if birthplace:
                return birthplace.strip()

        return ''

    def get_ethnicity(self, response):
        if 'ethnicity' in self.selector_map:
            ethnicity = self.process_xpath(response, self.get_selector_map('ethnicity')).get()
            if ethnicity:
                return ethnicity.strip()

        return ''

    def get_nationality(self, response):
        if 'nationality' in self.selector_map:
            nationality = self.process_xpath(response, self.get_selector_map('nationality')).get()
            if nationality:
                return nationality.strip()

        return ''

    def get_eyecolor(self, response):
        if 'eyecolor' in self.selector_map:
            eyecolor = self.process_xpath(response, self.get_selector_map('eyecolor')).get()
            if eyecolor:
                return eyecolor.strip()

        return ''

    def get_haircolor(self, response):
        if 'haircolor' in self.selector_map:
            haircolor = self.process_xpath(response, self.get_selector_map('haircolor')).get()
            if haircolor:
                return haircolor.strip()

        return ''

    def get_height(self, response):
        if 'height' in self.selector_map:
            height = self.process_xpath(response, self.get_selector_map('height')).get()
            if height:
                return height.strip()

        return ''

    def get_weight(self, response):
        if 'weight' in self.selector_map:
            weight = self.process_xpath(response, self.get_selector_map('weight')).get()
            if weight:
                return weight.strip()

        return ''

    def get_measurements(self, response):
        if 'measurements' in self.selector_map:
            measurements = self.process_xpath(response, self.get_selector_map('measurements')).get()
            if measurements:
                return measurements.strip()

        return ''

    def get_tattoos(self, response):
        if 'tattoos' in self.selector_map:
            tattoos = self.process_xpath(response, self.get_selector_map('tattoos')).get()
            if tattoos:
                return tattoos.strip()

        return ''

    def get_piercings(self, response):
        if 'piercings' in self.selector_map:
            piercings = self.process_xpath(response, self.get_selector_map('piercings')).get()
            if piercings:
                return piercings.strip()

        return ''

    def get_cupsize(self, response):
        if 'cupsize' in self.selector_map:
            cupsize = self.process_xpath(response, self.get_selector_map('cupsize')).get()
            if cupsize:
                return cupsize.strip()

        return ''

    def get_fakeboobs(self, response):
        if 'fakeboobs' in self.selector_map:
            fakeboobs = self.process_xpath(response, self.get_selector_map('fakeboobs')).get()
            if fakeboobs:
                return fakeboobs.strip()

        return ''

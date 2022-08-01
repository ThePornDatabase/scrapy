# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SceneItem(scrapy.Item):
    title = scrapy.Field()
    description = scrapy.Field()
    site = scrapy.Field()
    date = scrapy.Field()
    image = scrapy.Field()
    image_blob = scrapy.Field()
    performers = scrapy.Field()
    tags = scrapy.Field()
    url = scrapy.Field()
    id = scrapy.Field()
    trailer = scrapy.Field()
    parent = scrapy.Field()
    network = scrapy.Field()

class MovieItem(scrapy.Item):
    title = scrapy.Field()
    description = scrapy.Field()
    site = scrapy.Field()
    network = scrapy.Field()
    date = scrapy.Field()
    front = scrapy.Field()
    front_blob = scrapy.Field()
    back = scrapy.Field()
    back_blob = scrapy.Field()
    performers = scrapy.Field()
    tags = scrapy.Field()
    url = scrapy.Field()
    id = scrapy.Field()
    trailer = scrapy.Field()
    studio = scrapy.Field()
    director = scrapy.Field()
    format = scrapy.Field()
    length = scrapy.Field()
    year = scrapy.Field()
    rating = scrapy.Field()
    sku = scrapy.Field()
    upc = scrapy.Field()

class PerformerItem(scrapy.Item):
    name = scrapy.Field()
    network = scrapy.Field()
    url = scrapy.Field()
    image = scrapy.Field()
    image_blob = scrapy.Field()
    bio = scrapy.Field()
    gender = scrapy.Field()
    birthday = scrapy.Field()
    astrology = scrapy.Field()
    birthplace = scrapy.Field()
    ethnicity = scrapy.Field()
    nationality = scrapy.Field()
    haircolor = scrapy.Field()
    weight = scrapy.Field()
    height = scrapy.Field()
    measurements = scrapy.Field()
    tattoos = scrapy.Field()
    piercings = scrapy.Field()
    cupsize = scrapy.Field()
    fakeboobs = scrapy.Field()
    eyecolor = scrapy.Field()

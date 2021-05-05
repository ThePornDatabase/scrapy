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
    performers = scrapy.Field()
    tags = scrapy.Field()
    url = scrapy.Field()
    id = scrapy.Field()
    trailer = scrapy.Field()
    parent = scrapy.Field()
    network = scrapy.Field()

class PerformerItem(scrapy.Item):
    name = scrapy.Field()

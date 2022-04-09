# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import re

import scrapy
from pymongo import MongoClient
from scrapy import signals
from scrapy.exceptions import IgnoreRequest


class TpdbSceneDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()

        cls.crawler = crawler

        if crawler.settings['ENABLE_MONGODB']:
            db = MongoClient(crawler.settings['MONGODB_URL'])
            cls.db = db['scrapy']

        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        if re.search(spider.get_selector_map('external_id'), request.url) is None:
            return None

        if spider.force is True:
            return None

        # Used in production - we store the scene in MongoDB for caching reasons
        if self.crawler.settings['ENABLE_MONGODB']:
            result = self.db.scenes.find_one({'url': request.url})
            if result is not None and ('api_response' not in result or not result['api_response']):
                raise IgnoreRequest

        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class TpdbPerformerDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()

        cls.crawler = crawler

        if crawler.settings['ENABLE_MONGODB']:
            db = MongoClient(crawler.settings['MONGODB_URL'])
            cls.db = db['scrapy']

        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        if re.search(spider.get_selector_map('external_id'), request.url) is None:
            return None

        if spider.force is True:
            return None

        # Used in production - we store the scene in MongoDB for caching reasons
        if self.crawler.settings['ENABLE_MONGODB']:
            result = self.db.performers.find_one({'url': request.url})
            if result is not None and ('api_response' not in result or not result['api_response']):
                raise IgnoreRequest

        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

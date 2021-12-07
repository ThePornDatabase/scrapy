from scrapy.http import TextResponse

from tpdb.helpers.scrapy_dpath import DPathResponse


class DPathMiddleware(object):
    def process_response(self, request, response, spider):
        if isinstance(response, TextResponse):
            return DPathResponse(request, response)

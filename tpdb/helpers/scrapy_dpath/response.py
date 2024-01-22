from scrapy.http import TextResponse

from tpdb.helpers.scrapy_dpath.dpath import ScrapyDPath


class DPathResponse(TextResponse):
    request = None
    response = None

    def __init__(self, request, response):
        self.request = request
        self.response = response

        super(DPathResponse, self).__init__(response.url,
                                            status=response.status,
                                            headers=response.headers,
                                            body=response.body,
                                            flags=response.flags,
                                            request=response.request,
                                            certificate=response.certificate,
                                            ip_address=response.ip_address,
                                            protocol=response.protocol)

    def dpath(self, selector):
        return ScrapyDPath(self.response.json(), selector)

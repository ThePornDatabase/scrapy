from tpdb.helpers.flare_solverr import FlareSolverr
from tpdb.helpers.scrapy_flare import FlareRequest, FlareResponse


class FlareMiddleware(object):
    def __init__(self, crawler, flare_solverr):
        self.crawler = crawler
        self.flare_solverr = flare_solverr

    @classmethod
    def from_crawler(cls, crawler):
        s = crawler.settings
        flare_url = s.get('FLARE_URL', '')
        flare_solverr = FlareSolverr(flare_url)

        return cls(crawler, flare_solverr)

    def process_request(self, request, spider):
        if request.url == self.flare_solverr.get_api_url():
            return

        new_request = FlareRequest(request.url,
                                   self.flare_solverr,
                                   method=request.method,
                                   meta=request.meta,
                                   callback=request.callback,
                                   priority=request.priority)

        return new_request

    def process_response(self, request, response, spider):
        if request.url != self.flare_solverr.get_api_url():
            return request

        new_response = FlareResponse(response)
        return new_response

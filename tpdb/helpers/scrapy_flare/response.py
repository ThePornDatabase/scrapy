from scrapy.http import HtmlResponse


class FlareResponse(HtmlResponse):
    def __init__(self, response):
        resp = response.json()['solution']
        url = resp['url']
        status = resp['status']
        body = resp['response']

        super(FlareResponse, self).__init__(url, status=status, body=body, encoding='UTF-8', request=response.request)

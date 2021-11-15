import requests

from requests.models import Response
from requests.cookies import cookiejar_from_dict


class Http:
    @staticmethod
    def request(method, url, **kwargs):
        req = None
        try:
            req = requests.request(method, url, **kwargs)
        except:
            pass

        return req

    @staticmethod
    def get(url, **kwargs):
        Http.request('GET', url, **kwargs)

    @staticmethod
    def post(url, **kwargs):
        Http.request('POST', url, **kwargs)

    @staticmethod
    def head(url, **kwargs):
        Http.request('HEAD', url, **kwargs)

    @staticmethod
    def fake_response(req, url, status_code, content, headers={}, cookies={}):
        response = req
        if response is None:
            response = Response()

        response.url = url
        response.status_code = status_code
        response._content = content.encode('UTF-8') if content else ''
        response.headers = headers
        response.cookies = cookiejar_from_dict(cookies)

        return response

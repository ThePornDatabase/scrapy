import requests

from requests.models import Response
from requests.cookies import cookiejar_from_dict


class Http:
    @staticmethod
    def request(method: str, url: str, **kwargs):
        req = None
        try:
            req = requests.request(method, url, **kwargs)
        except:
            pass

        return req

    @staticmethod
    def get(url: str, **kwargs):
        return Http.request('GET', url, **kwargs)

    @staticmethod
    def post(url: str, **kwargs):
        return Http.request('POST', url, **kwargs)

    @staticmethod
    def head(url: str, **kwargs):
        return Http.request('HEAD', url, **kwargs)

    @staticmethod
    def fake_response(url: str, status_code: int, content: str | bytes, headers: dict, cookies: dict) -> Response:
        content = content if isinstance(content, bytes) else content.encode('UTF-8')
        cookies = {} if cookies is None else cookies
        headers = {} if headers is None else headers

        response = Response()
        response.url = url
        response.status_code = status_code
        response._content = content
        response.headers = headers
        response.cookies = cookiejar_from_dict(cookies)

        return response

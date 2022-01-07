import json
from urllib.parse import urlparse
from scrapy import Request


class FlareRequest(Request):
    def __init__(self,
                 url,
                 flare_solverr=None,
                 callback=None,
                 method='GET',
                 cookies=None,
                 meta=None,
                 **kwargs):

        if not flare_solverr:
            return

        method = method.lower()
        params = {
            'cmd': f'request.{method}',
            'session': flare_solverr.get_session(),
            'url': url,
        }

        if cookies:
            domain = urlparse(url).hostname
            if isinstance(cookies, dict):
                cookies = [{'name': name, 'value': value, 'domain': domain} for name, value in cookies.items()]
            params['cookies'] = cookies

        super(FlareRequest, self).__init__(url=flare_solverr.get_api_url(),
                                           method='POST',
                                           callback=callback,
                                           meta=meta,
                                           body=json.dumps(params),
                                           headers={'Content-Type': 'application/json'},
                                           **kwargs)

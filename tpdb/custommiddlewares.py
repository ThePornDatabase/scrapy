from w3lib.http import basic_auth_header


class CustomProxyMiddleware(object):
    def process_request(self, request, spider):
        # ~ request.meta['proxy'] = 'http://xxx.xxx.xxx.xxx:xxxx'
        request.meta['proxy'] = ''

from w3lib.http import basic_auth_header


class CustomProxyMiddleware(object):
    def process_request(self, request, spider):
        # ~ request.meta['proxy'] = 'http://192.168.1.151:8118'
        request.meta['proxy'] = ''

from scrapy.utils.project import get_project_settings


class CustomProxyMiddleware(object):
    settings = get_project_settings()
    if 'PROXY_ADDRESS' in settings.attributes.keys():
        proxy_address = settings.get('PROXY_ADDRESS')
    else:
        proxy_address = None

    if 'USE_PROXY' in settings.attributes.keys():
        use_proxy = settings.get('USE_PROXY')
    else:
        use_proxy = None

    def process_request(self, request, spider):

        if 'proxy' not in request.meta:
            if self.use_proxy:
                request.meta['proxy'] = self.proxy_address
            else:
                request.meta['proxy'] = ''

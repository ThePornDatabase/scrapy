#!/usr/bin/python3

import inspect
import os

from urllib.parse import urlparse

from scrapy import spiderloader
from scrapy.utils import project
from mdutils.mdutils import MdUtils


class Generator:
    mdFile = ''

    @staticmethod
    def loop_spiders():
        data = [
            'Network',
            'Parent',
            'URL',
            'Class',
        ]

        settings = project.get_project_settings()
        spider_loader = spiderloader.SpiderLoader.from_settings(settings)
        spiders = spider_loader.list()
        for spider in spiders:
            spider_class = spider_loader.load(spider)

            start_urls = ['']
            if hasattr(spider_class, 'start_urls'):
                start_urls = [urlparse(url) for url in spider_class.start_urls if isinstance(url, str)]
                start_urls = ['%s://%s' % (url.scheme, url.hostname) for url in start_urls]

            for url in start_urls:
                data.extend([
                    spider_class.network.title() if hasattr(spider_class, 'network') else '',
                    spider_class.parent.title() if hasattr(spider_class, 'parent') else '',
                    url,
                    os.path.basename(inspect.getfile(spider_class))
                ])

        return data

    def main(self):
        md_file = MdUtils(file_name='sitelist', title='Scraper Site List')
        md_file.new_header(level=1, title='Sites')
        data = self.loop_spiders()
        md_file.new_line()
        md_file.new_table(columns=4, rows=int(len(data) / 4), text=data, text_align='center')
        md_file.create_md_file()


if __name__ == '__main__':
    g = Generator()
    g.main()

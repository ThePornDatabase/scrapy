#!/usr/bin/python3

from scrapy import spiderloader
from scrapy.utils import project
from mdutils.mdutils import MdUtils
import inspect
import sys, os

class Generator():
    
    mdFile = ''

    def loop_spiders(self):
        data = [
            "Network",
            "Parent",
            "URL",
            "Class"
        ]
        settings = project.get_project_settings()
        spider_loader = spiderloader.SpiderLoader.from_settings(settings)
        spiders = spider_loader.list()
        for spider in spiders:
            spider_class = spider_loader.load(spider)
            if not hasattr(spider_class, 'start_urls'):
                data.extend([
                    spider_class.network if hasattr(spider_class, 'network') else '',
                    spider_class.parent if hasattr(spider_class, 'parent') else '',
                    '',
                    os.path.basename(inspect.getfile(spider_class))
                ])
                continue

            for url in spider_class.start_urls:
                data.extend([
                    spider_class.network.title() if hasattr(spider_class, 'network') else '',
                    spider_class.parent.title() if hasattr(spider_class, 'parent') else '',
                    url,
                    os.path.basename(inspect.getfile(spider_class))
                ])
        
        return data
            

    def main(self):
        mdFile = MdUtils(file_name='sitelist',title='Scraper Site List')
        mdFile.new_header(level=1, title='Sites')
        data = self.loop_spiders()
        mdFile.new_line()
        mdFile.new_table(columns=4, rows=int(len(data)/4), text=data, text_align='center')
        mdFile.create_md_file()



if __name__ == '__main__':
    g = Generator()
    g.main()

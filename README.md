# Scrapy for TPDB

This is the scrapy framework for TPDB's scraper.

### Installation

Clone this repo

``git clone --recurse-submodules https://github.com/ThePornDatabase/scrapy.git``

Install the packages using poetry

``poetry install``

You can then run a scraper using `scrapy crawl `**ScraperName**

``poetry run scrapy crawl Vixen``

### How it works

Each scraper is in it's own Python file, placed in the tpdb/spiders folder - they are stored in another repository so
people can contribute.


# Site Lists

[sitelist.md](sitelist.md)

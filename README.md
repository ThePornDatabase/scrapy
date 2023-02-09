# Scrapy for TPDB

This is the scrapy framework for TPDB's scraper.

### Installation

Clone this repo

``git clone --recurse-submodules https://github.com/ThePornDatabase/scrapy.git``

Install the packages using poetry

``poetry install``

Next change directory to `tpdb` and create a copy of example settings and edit if necessary:

```
cd tpdb
cp settings.py.example settings.py
```

You can then run a scraper using `scrapy crawl` **ScraperName**

``poetry run scrapy crawl Vixen``

### How it works

Each scraper is in it's own Python file, placed in the tpdb/spiders folder - they are stored in another repository so
people can contribute.


# Site Lists

[sitelist.md](sitelist.md)

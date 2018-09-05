#!/usr/bin/python
# -*- coding: UTF-8 -*-

from scrapy import cmdline

# 实时数据爬取
cmdline.execute("scrapy crawl hudongyi_sz".split())

# 以下2种爬取历史数据比较理想，对于爬实时数据不科学

# cmdline.execute("scrapy crawl hudongyi_sz_now".split())

# cmdline.execute("scrapy crawl hudongyi_sz_history".split())

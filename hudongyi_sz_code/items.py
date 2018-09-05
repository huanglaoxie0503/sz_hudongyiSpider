# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class HudongyiSzCodeItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    # 问题id
    questionId = scrapy.Field()
    # 提问者
    questioner = scrapy.Field()
    # 提问时间
    questionTime = scrapy.Field()
    # 提问内容/问题
    questionContent = scrapy.Field()

    # 回复时间
    replyTime = scrapy.Field()
    # 回复内容
    replyContent = scrapy.Field()
    # 公司代码
    stockCode = scrapy.Field()
    # 公司简称
    shortName = scrapy.Field()
    # 入库时间
    db_write_time = scrapy.Field()

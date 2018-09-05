# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql
import logging
from scrapy.exporters import JsonItemExporter

from .settings import MYSQL_TABLE
from .settings import MYSQL_HOST
from .settings import MYSQL_USER
from .settings import MYSQL_PASSWORD
from .settings import MYSQL_DBNAME


class HudongyiSzCodePipeline(object):
    def process_item(self, item, spider):
        return item


class JsonExporterPipeline(object):
    '''
     用scrapy 提供的json export 导出json文件
    '''

    def __init__(self):
        self.file = open('sz.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self,spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self,item,spider):
        self.exporter.export_item(item)
        return item


class MysqlPipeline(object):
    '''同步的方式将数据保存到数据库'''

    def __init__(self):
        self.conn = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db=MYSQL_DBNAME,
                                    charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
       try:
           # 更新
           # self.update(item)

           # 插入
           self.insert(item)

       except pymysql.Error as e:
           logging.error('-----------------insert faild-----------')
           logging.error(item['questionId'])
           logging.error(item['shortName'])
           logging.error(item['stockCode'])
           logging.error(e)
           print(e)

       return item

    def close_spider(self,spider):
        try:
            self.conn.close()
            logging.info('mysql already close')
        except Exception as e:
            logging.info('--------mysql no close-------')
            logging.error(e)

    def insert(self,item):
        try:
            insert_sql = """
                               insert into {0}(questionId,questioner,stockCode,shortName,questionContent,replyContent,questionTime,replyTime,last_time)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                               ON DUPLICATE KEY UPDATE questionId=VALUES(questionId),questioner=VALUES (questioner),stockCode=VALUES (stockCode),shortName=VALUES (shortName),
                               questionContent=VALUES (questionContent),replyContent=VALUES (replyContent),questionTime=VALUES (questionTime),
                               replyTime=VALUES (replyTime),last_time=VALUES (last_time)
                               """.format(MYSQL_TABLE)

            parms = (
                item['questionId'], item['questioner'],item['stockCode'], item['shortName'], item['questionContent'],
                item['replyContent'],item['questionTime'], item['replyTime'],item['db_write_time']
            )
            self.cursor.execute(insert_sql, parms)
            self.conn.commit()
            logging.info('----------------insert success-----------')
        except pymysql.Error as e:
            print(e)

    def update(self,item):
        '''
        按照问题id更新数据
        :param item:
        :return:
        '''
        try:
            update_sql="UPDATE {0} SET questionContent =%s ,replyContent=%s ,questioner=%s WHERE questionId =%s".format(MYSQL_TABLE)
            parms = (
                item['questionContent'],item['replyContent'],item['questioner'],item['questionId']
            )
            self.cursor.execute(update_sql, parms)
            self.conn.commit()
            logging.info('----------------update success-----------')
        except pymysql.Error as e:
            print(e)
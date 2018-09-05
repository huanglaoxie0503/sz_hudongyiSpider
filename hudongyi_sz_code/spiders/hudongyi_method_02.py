# -*- coding: utf-8 -*-
import scrapy
import re
import logging
from datetime import datetime,date,timedelta
from hudongyi_sz_code.items import HudongyiSzCodeItem
from hudongyi_sz_code.common import parse_datetime

logging.basicConfig(
    filename="sz.log",
    level=logging.INFO,
    format="%(asctime)-15s %(levelname)s %(filename)s %(lineno)d %(process)d %(message)s",
)


class HudongyiSzSpider(scrapy.Spider):
    name = "hudongyi_sz"
    allowed_domains = ["irm.cninfo.com.cn"]

    def start_requests(self):
        dtEnd = date.today()  # 当前时间
        dtStart = dtEnd + timedelta(days=-1)
        url='http://irm.cninfo.com.cn/ircs/interaction/lastRepliesForSzse.do'
        for pageNo in range(1,4):
            logging.info('正在抓取{0}页，日期为：{1}'.format(pageNo,dtEnd.__format__('%Y-%m-%d')))
            data={
                "condition.dateFrom": dtStart.__format__('%Y-%m-%d'),
                "condition.dateTo": dtEnd.__format__('%Y-%m-%d'),
                "condition.stockcode":"",
                "condition.keyWord":"",
                "condition.status":"",
                "condition.searchType": "code",
                "condition.questionCla": "",
                "condition.questionAtr": "",
                "condition.marketType": "Z",
                "condition.searchRange": "",
                "condition.questioner": "",
                "condition.questionerType": "",
                "condition.loginId": "",
                "condition.provinceCode": "",
                "condition.plate": "",
                "pageNo": str(pageNo),
                "categoryId": "",
                "code": "",
                "pageSize": "10",
                "source": "2",
                "requestUri": "/ircs/interaction/lastRepliesForSzse.do",
                "requestMethod": "POST"
            }

            yield scrapy.FormRequest(url,formdata=data,callback=self.parse_url_list)

    def parse_url_list(self,response):
        url = response.xpath('//a[@class="cntcolor"]/@href').extract()
        url_list = list(set(url))
        detail_url_list= list(map(lambda x: 'http://irm.cninfo.com.cn/ircs/interaction/' + x, url_list))
        for url in detail_url_list:
            yield scrapy.Request(url,self.parse_detail_content)

    def parse_detail_content(self, response):
        # 问题解析
        url = response.url
        pattern = r"questionId=(\d+)"
        questionId = re.findall(pattern, url)[0]
        questionContent = response.xpath(
            '//div[@class="askBoxOuter"]/div[@class="msgBox"]/div[@class="msgCnt cntcolor"]/div/text()'
        ).extract()
        questionContent = "".join(questionContent).strip()
        questionTime = response.xpath(
            '//div[@class="pubInfoask2"]/a[@class="date"]/text()'
        ).extract_first()
        questionTime = parse_datetime.parse_time(questionTime)

        questioner = response.xpath(
            '//div[@class="clear answerBoxOuter"]/div[@class="answerBox"]/div[@class="msgCnt cntcolor"]/a[2]/text()'
        ).extract_first()

        contents = response.xpath('//div[@class="clear answerBoxOuter"]')
        i = 0
        for content in contents:
            # 如果有多条回复，选取最新回复
            i = i + 1
            if i > 1:
                return
            # 回答内容解析
            stockCode = content.xpath(
                './/span[@class="comCode"]/a/text()'
            ).extract_first()
            shortName = content.xpath(
                './/span[@class="comName"]/a/text()'
            ).extract_first()
            replyTime = content.xpath(
                './/span[@class="time"]/a[@class="date"]/text()'
            ).extract_first()
            replyTime = parse_datetime.parse_time(replyTime)
            replyContent = content.xpath(
                './/div[@class="msgCnt cntcolor"]/text()'
            ).extract()
            replyContent = (
                "".join(replyContent)
                .strip()
                .lstrip()
                .replace("\n", "")
                .replace("\r", "")
                .replace(":", "")
                .replace("	                                    	", "")
            )

            Id = parse_datetime.get_question_id(questionId)
            if Id:
                logging.info("本条问答已经入库，问答id为：{0}".format(Id))
                return

            db_write_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            item = HudongyiSzCodeItem()
            item["questionId"] = questionId
            item["questioner"]=questioner
            item["questionTime"] = questionTime
            item["questionContent"] = questionContent
            item["replyTime"] = replyTime
            item["replyContent"] = replyContent
            item["stockCode"] = stockCode
            item["shortName"] = shortName
            item['db_write_time']=db_write_time
            yield item
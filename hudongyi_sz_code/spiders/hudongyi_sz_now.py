# -*- coding: utf-8 -*-
import scrapy
import re
import logging

from hudongyi_sz_code.items import HudongyiSzCodeItem
from hudongyi_sz_code.common import parse_datetime

logging.basicConfig(
    filename="szhudongyi.log",
    level=logging.INFO,
    format="%(asctime)-15s %(levelname)s %(filename)s %(lineno)d %(process)d %(message)s",
)


class HudongyiSzSpider(scrapy.Spider):
    """
            处理深圳互动易实时数据
    """

    name = "hudongyi_sz_now"
    allowed_domains = ["irm.cninfo.com.cn"]

    def start_requests(self):
        # 获取深交所公司代码列表
        codes = parse_datetime.get_stock_from_db()
        for code in codes:
            url_base = "http://irm.cninfo.com.cn/ircs/interaction/lastRepliesforSzseSsgs.do?condition.type=1&condition.stockcode={0}&condition.stocktype=S".format(
                code
            )
            data = {
                "condition.searchType": "code",
                "pageNo": "1",
                "categoryId": "",
                "code": "",
                "pageSize": "10",
                "source": "2",
                "requestUri": "/ircs/interaction/lastRepliesforSzseSsgs.do",
                "requestMethod": "POST",
            }
            yield scrapy.FormRequest(
                url_base, formdata=data, callback=self.parse, meta={"code": code}
            )

    def parse(self, response):
        """
        1.解析问答内容列表也：解析出每一条问答的链接，传递给详情页解析
        2.实时数据抓取，每隔30分钟抓一次，故无需做翻页处理，历史数据专门有处理程序
        :param response:
        :return:
        """
        # 如果页面解析出No data ，则说明该公司没有问答数据
        if response.xpath('//div[@align="center"]/text()').extract_first() == "No data":
            print("no content")
            return

        infos = response.xpath('//li[@class="gray"]')
        for info in infos:
            detail_url = (
                "http://irm.cninfo.com.cn/ircs/interaction/"
                + info.xpath('.//a[@class="ask"]/@href').extract_first()
            )
            reply_time = (
                info.xpath('.//a[@class="date"]/text()').extract_first().strip()
            )
            replyTime = parse_datetime.parse_time(reply_time)
            # 该条信息回复时间和数据库同一个公司最大回复时间比较，如果小于则返回，不入库
            stockCode = response.meta.get("code")
            max_time = parse_datetime.get_max_time(stockCode)
            if max_time:
                if replyTime <= max_time:
                    logging.info(
                        "最新回复时间为：{0},小于或等于数据库最大时间:{1},因此{2}没有最新回复".format(
                            replyTime, max_time, stockCode
                        )
                    )
                    return
            yield scrapy.Request(detail_url, callback=self.detail_parse)

    def detail_parse(self, response):
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
        # questioner = response.xpath(
        #     '//div[@class="askBoxOuter"]/div[@class="userPic"]/a/span/text()'
        # ).extract_first()
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

            item = HudongyiSzCodeItem()
            item["questionId"] = questionId
            item["questioner"]=questioner
            item["questionTime"] = questionTime
            item["questionContent"] = questionContent
            item["replyTime"] = replyTime
            item["replyContent"] = replyContent
            item["stockCode"] = stockCode
            item["shortName"] = shortName

            yield item

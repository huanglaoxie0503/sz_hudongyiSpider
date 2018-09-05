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
        处理深圳互动易历史数据
    """

    name = "hudongyi_sz_history"
    allowed_domains = ["irm.cninfo.com.cn"]

    def start_requests(self):
        # 获取深交所公司代码列表
        codes = parse_datetime.get_stock_from_db()
        for code in codes:
            url_base = "http://irm.cninfo.com.cn/ircs/interaction/lastRepliesforSzseSsgs.do?condition.type=1&condition.stockcode={0}&condition.stocktype=S".format(
                code
            )
            pageNo = 1
            data = {
                "condition.searchType": "code",
                "pageNo": str(pageNo),
                "categoryId": "",
                "code": "",
                "pageSize": "10",
                "source": "2",
                "requestUri": "/ircs/interaction/lastRepliesforSzseSsgs.do",
                "requestMethod": "POST",
            }
            yield scrapy.FormRequest(
                url_base,
                formdata=data,
                callback=self.parse,
                meta={"pageNo": pageNo, "code": code},
            )

    def parse(self, response):
        """
        1.解析问答内容
        2.处理翻页请求情况
        :param response:
        :return:
        """
        # 如果页面解析出No data ，则说明该公司没有问答数据
        if response.xpath('//div[@align="center"]/text()').extract_first() == "No data":
            print("no content")
            return
        # 抓取页面最大页数，作为抓取停止标志
        max_page_log = re.findall(r"javascript:toPage\S+\;", response.text)
        if max_page_log:
            # 取倒数第二个
            max_page_item = max_page_log[-2]
            max_page = re.findall(r"(\d+)", max_page_item)[0]
        else:
            max_page = 1

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

        # 下一页:翻页处理
        cur_page = response.meta.get("pageNo")
        cur_code = response.meta.get("code")
        # 如果当前页数大于最大页数，则返回退出
        if cur_page > int(max_page):
            logging.info("{0}公司最后一也有13条数据,已经抓取完毕！".format(cur_code))
            return

        if len(infos) == 13:
            print(
                str(cur_page) + "-----" + str(cur_code) + "---max_page:" + str(max_page)
            )
            next_page = cur_page + 1
            data = {
                "condition.searchType": "code",
                "pageNo": str(next_page),
                "categoryId": "",
                "code": "",
                "pageSize": "10",
                "source": "2",
                "requestUri": "/ircs/interaction/lastRepliesforSzseSsgs.do",
                "requestMethod": "POST",
            }
            cur_url = "http://irm.cninfo.com.cn/ircs/interaction/lastRepliesforSzseSsgs.do?condition.type=1&condition.stockcode={0}&condition.stocktype=S".format(
                cur_code
            )

            yield scrapy.FormRequest(
                cur_url,
                formdata=data,
                callback=self.parse,
                meta={"pageNo": next_page, "code": cur_code},
            )

    def detail_parse(self, response):
        # 问题内容解析
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

# <200 http://irm.cninfo.com.cn/ircs/interaction/viewQuestionForSzseSsgs.do?questionId=5951881&condition.replyOrderType=1&condition.searchRange=0>
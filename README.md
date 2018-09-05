环境：python3、 scrapy 、pymysql 、re、fake_useragent
项目介绍：抓取深交所互动易问答数据。
Url链接（例子）:http://irm.cninfo.com.cn/ircs/interaction/lastRepliesforSzseSsgs.do?condition.type=1&condition.stockcode=000001&condition.stocktype=S

1.两种抓取思路：
# 实时数据爬取 ，比较科学
hudongyi_method_02.py：由互动易实时更新问答数据官网，抓取最新数据
 # 以下爬取历史数据比较理想，对于爬实时数据不科学，不必要的请求太多
 hudongyi_sz_history.py:抓取历史数据
 hudongyi_sz_now.py：由公司代码进入互动易该公司主页，抓取最新的问答数据
   

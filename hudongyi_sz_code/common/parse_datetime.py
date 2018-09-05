import datetime
import pymysql

from hudongyi_sz_code.settings import MYSQL_HOST
from hudongyi_sz_code.settings import MYSQL_USER
from hudongyi_sz_code.settings import MYSQL_PASSWORD
from hudongyi_sz_code.settings import MYSQL_DBNAME
from hudongyi_sz_code.settings import MYSQL_TABLE

from hudongyi_sz_code.settings import (
    mysql_host,
    mysql_user,
    mysql_password,
    mysql_db,
    mysql_table,
)

conn = pymysql.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    passwd=MYSQL_PASSWORD,
    db=MYSQL_DBNAME,
    charset="utf8",
)
cursor = conn.cursor()

conn_stock = pymysql.connect(
    host=mysql_host, user=mysql_user, passwd=mysql_password, db=mysql_db, charset="utf8"
)
cursor_stock = conn_stock.cursor()


def parse_time(str_time):
    """
    提问时间、答复时间解析
    :param str_time:
    :return:
    """
    try:
        result_time = str_time
        result_time = result_time.replace("（", "").replace("）", "")
        result_time = result_time.replace("年", "-").replace("月", "-").replace("日", "")
        datetime_result_time = datetime.datetime.strptime(result_time, "%Y-%m-%d %H:%M")

        return datetime_result_time
    except Exception as e:
        print(e)


def get_stock_from_db():
    """
        数据库获取深交所所有股票代码并返回
    :return: codes
    """
    try:
        codes = []
        sql = """SELECT stock_code FROM {0} WHERE stock_code LIKE '%SZ';""".format(
            mysql_table
        )
        cursor_stock.execute(sql)
        recodes = cursor_stock.fetchall()
        for recode in recodes:
            code = recode[0].split(".")[0].strip()
            codes.append(code)
        return codes
    except pymysql.Error as e:
        print(e)


def get_max_time(code):
    """
        按公司代码从数据库获取做大时间并返回
    :param code:
    :return:
    """
    try:
        sql = "select max(replyTime) from {0} WHERE stockCode={1}".format(
            MYSQL_TABLE, code
        )
        cursor.execute(sql)
        max_time = cursor.fetchall()[0][0]
        return max_time
    except pymysql.Error as e:
        print(e)


def get_question_id(art_id):
    """验证question_id数据库是否已经存在"""
    try:
        sql = "select * from {0} where questionId=%s;".format(MYSQL_TABLE)
        cursor.execute(sql, (art_id,))
        results = cursor.fetchall()
        if results:
            return results[0][0]
        else:
            return None
    except pymysql.Error as e:
        print(e)


if __name__ == "__main__":
    get_max_time("000001")
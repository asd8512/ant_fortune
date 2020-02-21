import datetime
import json
from decimal import Decimal

import requests
from retrying import retry

from ant_fortune.east_money.models import Fund, FundHistory


class FetchFund(object):
    """ 获取天天基金数据 """

    def __init__(self):
        # favor
        self.favor_url = "https://api.fund.eastmoney.com/Favor/Get"
        self.favor_cookie = "EMFUND1=null; Eastmoney_Fund_Transform=true; EMFUND0=null; EMFUND2=02-14%2010%3A33%3A20@%23%24%u4E07%u5BB6%u7ECF%u6D4E%u65B0%u52A8%u80FD%u6DF7%u5408C@%23%24005312; EMFUND3=02-13%2010%3A37%3A43@%23%24%u94F6%u6CB3%u5BB6%u76C8%u503A%u5238@%23%24006761; EMFUND4=02-13%2011%3A27%3A12@%23%24%u6C47%u4E30%u664B%u4FE1%u667A%u9020%u5148%u950B%u80A1%u7968C@%23%24001644; EMFUND5=02-13%2015%3A24%3A44@%23%24%u56FD%u6CF0CES%u534A%u5BFC%u4F53%u884C%u4E1AETF%u8054%u63A5A@%23%24008281; EMFUND6=02-13%2015%3A31%3A49@%23%24%u5B9D%u76C8%u6D88%u8D39%u4E3B%u9898%u6DF7%u5408@%23%24003715; EMFUND7=02-14%2010%3A30%3A38@%23%24%u4E2D%u6B27%u884C%u4E1A%u6210%u957F%u6DF7%u5408%28LOF%29C@%23%24004231; Eastmoney_Fund=008282_004231_003715_007579_005963_003096_519005_000717_007883_005312_001740_006757_160225_020022_003593_007835_000963_003397_270050_161903_360016_007164_002482_000573_007824_007853_007301_519195_001766_004857_519674_161122_110011_002264; st_si=23151148569795; st_asi=delete; EMFUND9=02-14%2010%3A44%3A04@%23%24%u5149%u5927%u4E2D%u56FD%u5236%u90202025%u6DF7%u5408@%23%24001740; EMFUND8=02-16 17:13:55@#$%u56FD%u6CF0CES%u534A%u5BFC%u4F53%u884C%u4E1AETF%u8054%u63A5C@%23%24008282; st_pvi=09258696057425; st_sp=2020-01-06%2023%3A29%3A28; st_inirUrl=https%3A%2F%2Fwww.baidu.com%2Flink; st_sn=9; st_psi=20200216171517162-119146300572-6467219141"
        self.favor_referer = "http://favor.fund.eastmoney.com/"
        self.date = datetime.date.today()

    def _get(self, **kwargs):
        resp = requests.get(**kwargs)
        return resp

    # @retry(requests.exceptions.ConnectionError, delay=2)
    def fund_rank_data(self, start_date, end_date, page_index):
        resp = self._get(url=self.fund_rank_url(start_date=start_date, end_date=end_date, page_index=page_index))
        text = resp.text
        start, end = self.get_square_bracket_index(text)
        data = json.loads(text[start: end])
        return data

    def fund_rank_url(self, start_date, end_date, page_index):
        """
        基金排行url
        :param start_date: 2019-02-19
        :param end_date: 2019-02-19
        :param page_index: 1
        :return:
        """

        url = f"http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=all&rs=&gs=0&sc=zzf&st=desc&sd=" \
              f"{start_date}&ed={end_date}&qdii=&tabSubtype=,,,,,&pi={page_index}&pn=100&dx=1"

        return url

    def fetch_fund_history_data(self, fund_code):
        """ 获取基金历史数据 """

        url = self.fund_history_url(fund_code=fund_code)
        resp = self._get(url=url)
        text = resp.text
        data = json.loads(text)["datas"]

        return data

    def fund_history_url(self, fund_code):
        url = f"http://fundwebapi.eastmoney.com/FundWebJJBAPI/FundJJJZHis.aspx?bzdm={fund_code}&top=9999"

        return url

    def fetch_single_fund(self, fund_code):
        """ 获取单个基金信息，主要是为获取基金类型 """

        url = f"http://fundwebapi.eastmoney.com/FundWebJJBAPI/FundCompanyForFavorInfo.ashx?fcodes={fund_code}"
        resp = self._get(url=url)
        text = resp.text
        data = json.loads(text)["datas"][0]
        return data

    # def fetch_favor_data(self):
    #     """ 获取自选数据 """
    #
    #     headers = {"cookie": self.favor_cookie, "referer": self.favor_referer}
    #     resp = self._get(url=self.favor_url, headers=headers)
    #     data = json.loads(resp.text)
    #     kfs = data.get("Data").get("KFS")
    #     return kfs

    # def flush_favor_funds(self):
    #     """ 同步自选 """
    #
    #     kfs = self.fetch_favor_data()
    #     for kf in kfs:
    #         Fund.objects.get_or_create(
    #             short_name=kf.get("SHORTNAME"),
    #             fund_code=kf.get("FCODE"),
    #             fund_type=kf.get("FTYPE"),
    #         )
    #
    #     return

    # def fetch_single_data(self, fund_code):
    #     url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
    #     text = self._get(url=url).text
    #     start, end = self.get_index(text)
    #     try:
    #         data = json.loads(text[start: end])
    #     except json.decoder.JSONDecodeError:
    #         data = None
    #
    #     return data

    # def flush_history_data(self, ):
    #
    #     kfs = self.fetch_favor_data()
    #     for kf in kfs:
    #         fcode = kf.get("FCODE")
    #         gszzl = kf.get("gszzl")
    #         data = FundHistory.objects.filter(
    #             fund__fund_code=fcode,
    #             transaction_date=self.date,
    #         ).last()
    #         if data:
    #             data.gszzl = gszzl
    #             estimate_income = data.increase_rate / Decimal(100) * data.start_money
    #             data.estimate_income = estimate_income
    #             data.end_money = data.start_money + estimate_income
    #             data.save()
    #         else:
    #             fund = Fund.objects.get(fund_code=fcode)
    #             FundHistory.objects.create(
    #                 transaction_date=self.date,
    #                 accumulative_net_value=kf.get("gszzl"),
    #                 fund=fund,
    #             )

    def get_brace_index(self, text: str):
        """ 大括号 """

        start = text.find("{")
        end = text.find("}")
        return start, end + 1

    def get_square_bracket_index(self, text: str):
        """ 中括号 """

        start = text.find("[")
        end = text.find("]")
        return start, end + 1

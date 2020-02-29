import datetime

from ant_fortune.east_money.client import FetchFund


class CommonDataMixin(object):

    def __init__(self):
        self.today = datetime.date.today()
        self.fund_client = FetchFund()

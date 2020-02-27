from celery import shared_task

from ant_fortune.east_money.client import FetchFund


@shared_task
def fund_rank_data(start_date, end_date, page_index):
    data = FetchFund().fetch_fund_rank_data(start_date, end_date, page_index)
    return data


@shared_task
def single_fund(fund_code):
    data = FetchFund().fetch_single_fund(fund_code=fund_code)[6]
    return data

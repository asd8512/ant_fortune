import datetime

from celery import shared_task

from ant_fortune.east_money.client import FetchFund
from ant_fortune.east_money.models import Fund


@shared_task
def sync_funds_task(start_date, end_date, page_index):
    """ 同步所有基金数据 """

    while True:
        data = FetchFund().fetch_fund_rank_data(start_date=start_date, end_date=end_date, page_index=int(page_index))
        if not data:
            break
        fund_list = []
        for ele in data:
            i = ele.split(",")
            if i[3] in ["", " ", None]:
                i[3] = datetime.date.today()
            for v in i:
                if v in ["", " "]:
                    index = i.index(v)
                    i[index] = 0.0
            ret = Fund.objects.filter(code=i[0]).exists()
            fund_kwargs = dict(
                modified_date=i[3],
                unit_net_value=i[4],
                accumulative_net_value=i[5],
                daily_increase_date=i[6],
                recent_1_week=i[7],
                recent_1_month=i[8],
                recent_3_month=i[9],
                recent_6_month=i[10],
                recent_1_year=i[11],
                recent_2_year=i[12],
                recent_3_year=i[13],
                this_year=i[14],
                since_inception=i[15],
                establishment_date=i[16],
            )
            if ret:
                Fund.objects.filter(code=i[0]).update(**fund_kwargs)
            else:
                fund_list.append(
                    Fund(
                        code=i[0],
                        name=i[1],
                        initials=i[2],
                        fund_type=FetchFund().fetch_single_fund(fund_code=i[0])[6],
                        service_fee=i[20].strip("%"),
                        **fund_kwargs
                    )
                )
        page_index += 1
        Fund.objects.bulk_create(fund_list)
    return


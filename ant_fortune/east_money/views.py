import datetime

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ant_fortune.east_money.client import FetchFund
from ant_fortune.east_money.models import FundHistory, Fund, Favor, Stock
from ant_fortune.east_money.serializers import HistoryDataSerializer, FundSerializer, FavorSerializer, StockSerializer
from ant_fortune.east_money.tasks import fund_rank_data, single_fund


class StockViewSet(ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer


class FundViewSet(ModelViewSet):
    """ Fund """

    queryset = Fund.objects.all()
    serializer_class = FundSerializer
    filter_backends = ModelViewSet.filter_backends + [
        DjangoFilterBackend
    ]
    ordering_fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(FundViewSet, self).__init__(*args, **kwargs)
        self.date = datetime.date.today()
        self.client = FetchFund()

    @action(methods=["get"], detail=False)
    def test(self, request):
        return Response("It's ok.")

    @action(methods=["get"], detail=False)
    def sync_funds(self, request):
        """ 同步所有基金数据 """

        start_date = request.query_params.get("start_date") or self.date
        end_date = request.query_params.get("end_date") or self.date
        page_index = request.query_params.get("page_index") or 1
        while True:
            data = fund_rank_data(start_date=start_date, end_date=end_date, page_index=int(page_index)).delay()
            if not data:
                break
            fund_list = []
            for ele in data:
                i = ele.split(",")
                fund_type = single_fund(fund_code=i[0]).delay()
                if i[3] in ["", " ", None]:
                    i[3] = self.date
                for v in i:
                    if v in ["", " "]:
                        index = i.index(v)
                        i[index] = 0.0
                ret = Fund.objects.filter(code=i[0]).exists()
                if ret:
                    Fund.objects.filter(code=i[0]).update(
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
                else:
                    fund_list.append(
                        Fund(
                            code=i[0],
                            name=i[1],
                            initials=i[2],
                            fund_type=fund_type,
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
                            service_fee=i[20].strip("%"),
                        )
                    )
                Fund.objects.bulk_create(fund_list)
            page_index += 1

        return Response("syncing.")


class FundHistoryViewSet(ModelViewSet):
    """
        1. 更新每日数据
        2. 实时估算盈利值
        3. 连续跌势提醒
        4. 连续涨势提醒
    """
    queryset = FundHistory.objects.all()
    serializer_class = HistoryDataSerializer
    filter_backends = ModelViewSet.filter_backends + [
        DjangoFilterBackend
    ]
    ordering = ("start_money",)
    ordering_fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(FundHistoryViewSet, self).__init__(*args, **kwargs)
        self.date = datetime.date.today()
        self.client = FetchFund()

    @action(methods=["get"], detail=False)
    def sync_history(self, request):
        """ 同步基金历史数据 """

        funds = Fund.objects.values_list("id", "code")
        for fund in funds:
            history_list = []
            datas = self.client.fetch_fund_history_data(fund_code=fund[1])
            for data in datas:
                if data[1] == "-":
                    data[1] = 0.0
                if data[2] == "-":
                    data[2] = 0.0
                if data[3] == "-":
                    data[3] = "0.0%"
                history_list.append(
                    FundHistory(
                        transaction_date=data[0],
                        unit_net_value=data[1],
                        accumulative_net_value=data[2],
                        daily_increase_date=data[3].strip("%"),
                        fund_id=fund[0],
                    )
                )
                FundHistory.objects.bulk_create(history_list)

        return Response("syncing.")

    @action(methods=["get"], detail=False)
    def sync_favor_history(self):

        return Response("syncing.")

    # @action(methods=["get"], detail=False)
    # def estimate_income(self, request):
    #     """ 估算盈利 """
    #
    #     self.flush_today(request=request)
    #
    #     funds = Fund.objects.filter(
    #         is_hold=True,
    #         hold_money__gt=0,
    #     )
    #     history_data = self.queryset.filter(
    #         fund__in=funds,
    #         transaction_date=self.date,
    #         start_money__gte=0,
    #         increase_rate__isnull=False,
    #     )
    #     income = 0.0
    #     for data in history_data:
    #         rate = float(data.increase_rate) / 100
    #         hold_money = float(data.start_money)
    #         income += hold_money * rate
    #
    #     return Response(income)

    # @action(methods=["get"], detail=False)
    # def flush_today(self, request):
    #     """ 更新本日交易日数据 """
    #
    #     funds = Fund.objects.filter(
    #         is_hold=True,
    #         hold_money__gt=0,
    #     )
    #     for fund in funds:
    #         data = self.client.fetch_single_data(fund_code=fund.fund_code)
    #         if data is None:
    #             continue
    #         increase_rate = data.get("gszzl")
    #         history_data = FundHistory.objects.filter(
    #             fund=fund,
    #             transaction_date=self.date,
    #         ).last()
    #         if history_data:
    #             history_data.increase_rate = increase_rate
    #             history_data.save()
    #         else:
    #             history_data = FundHistory.objects.create(
    #                 fund=fund,
    #                 transaction_date=self.date,
    #                 start_money=fund.hold_money,
    #                 increase_rate=increase_rate,
    #             )
    #         history_data.calc_income()
    #     return Response("flush today's data complete.")


class FavorViewSet(ModelViewSet):
    queryset = Favor.objects.all()
    serializer_class = FavorSerializer

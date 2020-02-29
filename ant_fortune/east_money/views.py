from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ant_fortune.east_money.models import FundHistory, Fund, Favor, Stock
from ant_fortune.east_money.serializers import HistoryDataSerializer, FundSerializer, FavorSerializer, StockSerializer
from ant_fortune.east_money.tasks import sync_funds_task
from utils.common_data import CommonDataMixin


class StockViewSet(ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer


class FundViewSet(ModelViewSet, CommonDataMixin):
    """ Fund """

    queryset = Fund.objects.all()
    serializer_class = FundSerializer
    filter_backends = ModelViewSet.filter_backends + [
        DjangoFilterBackend
    ]
    ordering_fields = "__all__"

    @action(methods=["get"], detail=False)
    def test(self, request):
        return Response("It's ok.")

    @action(methods=["get"], detail=False)
    def sync_funds(self, request):
        start_date = request.query_params.get("start_date") or self.today
        end_date = request.query_params.get("end_date") or self.today
        page_index = request.query_params.get("page_index") or 1
        sync_funds_task.delay(start_date=start_date, end_date=end_date, page_index=page_index)
        return Response("syncing...")


class FundHistoryViewSet(ModelViewSet, CommonDataMixin):
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

    @action(methods=["get"], detail=False)
    def sync_history(self, request):
        """ 同步基金历史数据 """

        funds_id = Fund.objects.values_list("id", "code")
        self.process_create(funds_id=funds_id)

        return Response("syncing.")

    @action(methods=["get"], detail=False)
    def sync_favor_history(self):
        funds_id = Favor.objects.filter(content_type__model="fund").values_list("object_id", flat=True)
        self.process_create(funds_id=funds_id)
        return Response("syncing.")

    def process_create(self, funds_id):
        for fund in funds_id:
            history_list = []
            datas = self.fund_client.fetch_fund_history_data(fund_code=fund[1])
            for data in datas:
                data[1] = 0.0 if data[1] == "-" else 0.0
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
        return


class FavorViewSet(ModelViewSet, CommonDataMixin):
    queryset = Favor.objects.all()
    serializer_class = FavorSerializer

    @action(methods=["get"], detail=False)
    def estimate_income(self, request):
        """ 估算盈利 """

        self.flush_today(request=request)

        funds = Fund.objects.filter(
            is_hold=True,
            hold_money__gt=0,
        )
        history_data = self.queryset.filter(
            fund__in=funds,
            transaction_date=self.today,
            start_money__gte=0,
            increase_rate__isnull=False,
        )
        income = 0.0
        for data in history_data:
            rate = float(data.increase_rate) / 100
            hold_money = float(data.start_money)
            income += hold_money * rate

        return Response(income)

    @action(methods=["get"], detail=False)
    def flush_today(self, request):
        """ 更新本日交易日数据 """

        funds = Fund.objects.filter(
            is_hold=True,
            hold_money__gt=0,
        )
        for fund in funds:
            data = self.fund_client.fetch_single_data(fund_code=fund.fund_code)
            if data is None:
                continue
            increase_rate = data.get("gszzl")
            history_data = FundHistory.objects.filter(
                fund=fund,
                transaction_date=self.today,
            ).last()
            if history_data:
                history_data.increase_rate = increase_rate
                history_data.save()
            else:
                history_data = FundHistory.objects.create(
                    fund=fund,
                    transaction_date=self.today,
                    start_money=fund.hold_money,
                    increase_rate=increase_rate,
                )
            history_data.calc_income()
        return Response("flush today's data complete.")

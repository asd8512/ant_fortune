from django.contrib.contenttypes.models import ContentType
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from ant_fortune.east_money.models import FundHistory, Fund, Favor, Stock
from ant_fortune.east_money.serializers import HistoryDataSerializer, FundSerializer, FavorSerializer, StockSerializer
from ant_fortune.east_money.tasks import sync_funds_task
from utils.common_data import *


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

    @action(methods=["get"], detail=False)
    def test(self, request):
        return Response("It's ok.")

    @action(methods=["get"], detail=False)
    def sync_funds(self, request):
        start_date = request.query_params.get("start_date") or today
        end_date = request.query_params.get("end_date") or today
        page_index = request.query_params.get("page_index") or 1
        sync_funds_task.delay(start_date=start_date, end_date=end_date, page_index=page_index)
        return Response("syncing...")

    @action(methods=["get"], detail=False)
    def update_daily_rate(self, request):

        sync_funds_task.delay(start_date=today, end_date=today, page_index=1)
        self.perform_update_fund()
        return Response("ok.")

    @action(methods=["get"], detail=False)
    def update_daily_rate_loop(self, request):

        sync_funds_task.delay(start_date=today, end_date=today, page_index=1)

        while datetime.datetime.now() < datetime.datetime.now().replace(hour=15, minute=20):
            self.perform_update_fund()

        return Response("ok.")

    def perform_update_fund(self):
        funds_code = Fund.objects.values_list("code", flat=True)
        for fund_code in funds_code:
            data = fund_client.fetch_single_data(fund_code)
            if not data:
                continue
            print(f"---------code: {fund_code}---------")
            Fund.objects.filter(code=data["fundcode"]).update(
                modified_date=data["gztime"].split(" ")[0],
                daily_increase_rate=data["gszzl"]
            )


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
            datas = fund_client.fetch_fund_history_data(fund_code=fund[1])
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
                        daily_increase_rate=data[3].strip("%"),
                        fund_id=fund[0],
                    )
                )
                FundHistory.objects.bulk_create(history_list)
        return


class FavorViewSet(ModelViewSet):
    queryset = Favor.objects.all()
    serializer_class = FavorSerializer

    @action(methods=["post"], detail=False)
    def add(self, request):

        code = request.data.get("code")
        type_ = request.data.get("type")
        money = request.data.get("money")

        if code is None:
            return Response("Invalid code", 400)
        if type_ is None or (type_.lower() not in ["fund", "stock"]):
            return Response("Invalid type", 400)

        content_type = ContentType.objects.get(model=type_)
        try:
            obj = content_type.get_object_for_this_type(code=code)
            Favor.create(obj=obj, hold_money=money or 0.0)
        except (Fund.DoesNotExist, Stock.DoesNotExist):
            return Response("Wrong params.")
        return Response("add complete.")

    @action(methods=["get"], detail=False)
    def estimate_income(self, request):
        """ 估算盈利 """

        pass

        return Response()

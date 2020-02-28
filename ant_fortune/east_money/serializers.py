from rest_framework.serializers import ModelSerializer

from ant_fortune.east_money.models import FundHistory, Fund, Favor, Stock


class StockSerializer(ModelSerializer):
    class Meta:
        model = Stock
        fields = "__all__"


class FundSerializer(ModelSerializer):
    class Meta:
        model = Fund
        fields = "__all__"


class HistoryDataSerializer(ModelSerializer):
    class Meta:
        model = FundHistory
        fields = "__all__"


class FavorSerializer(ModelSerializer):
    class Meta:
        model = Favor
        fields = "__all__"

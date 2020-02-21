from rest_framework.serializers import ModelSerializer

from ant_fortune.east_money.models import FundHistory, Fund


class FundSerializer(ModelSerializer):
    class Meta:
        model = Fund
        fields = "__all__"


class HistoryDataSerializer(ModelSerializer):
    class Meta:
        model = FundHistory
        fields = "__all__"

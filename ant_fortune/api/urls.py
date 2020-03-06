from django.urls import path, include
from rest_framework import routers

from ant_fortune.east_money.views import FundHistoryViewSet, FundViewSet, FavorViewSet

router = routers.DefaultRouter(trailing_slash=False)

router.register(r"fund", FundViewSet)
router.register(r"history_data", FundHistoryViewSet)
router.register(r"favor", FavorViewSet)

urlpatterns = [
    path("", include(router.urls))
]

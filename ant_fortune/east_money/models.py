from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_extensions.db.models import TimeStampedModel

from utils.model import SoftDeleteMixin, SoftDeleteManager, SoftDeleteQuerySet


class Stock(models.Model):
    """ 股票 """

    name = models.CharField(max_length=255, blank=True, default=None)  # 股票名称
    code = models.CharField(max_length=15, blank=True, default=None)  # 股票代码

    modified_date = models.DateField(null=True, default=None)  # 数据更新日期
    daily_increase_rate = models.DecimalField(max_digits=14, decimal_places=2, default=0)  # 该交易日涨幅

    class Meta:
        db_table = "stocks"


class Fund(models.Model):
    """ 基金 """

    code = models.CharField(max_length=15, blank=True, default=None)  # 基金代码
    name = models.CharField(max_length=255, blank=True, default=None)  # 基金名称
    initials = models.CharField(max_length=31, blank=True, default=None)  # 名称字母
    fund_type = models.CharField(max_length=31, blank=True, default=None)  # 基金类型
    establishment_date = models.DateField(null=True, default=None)  # 基金创立日期

    modified_date = models.DateField(null=True, default=None)  # 数据更新日期
    unit_net_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)  # 单位净值
    accumulative_net_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)  # 累计净值
    daily_increase_date = models.DecimalField(max_digits=14, decimal_places=2, default=0)  # 日涨幅
    recent_1_week = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)  # 近1周
    recent_1_month = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)  # 近1月
    recent_3_month = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)  # 近3月
    recent_6_month = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)  # 近6月
    recent_1_year = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)  # 近1年
    recent_2_year = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)  # 近2年
    recent_3_year = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)  # 近3年
    this_year = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)  # 近年来
    since_inception = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)  # 成立来

    service_fee = models.DecimalField(max_digits=14, decimal_places=2, default=0.0)  # 服务费

    stocks = models.ManyToManyField(
        Stock,
        related_name="funds",
        db_constraint=False,
    )

    class Meta:
        db_table = 'funds'


# @receiver(pre_save, sender=Fund)
# def check_value(sender, **kwargs):
#     instance = kwargs.get("instance")
#     fields = ["recent_1_week", "recent_1_month", "recent_3_month", "recent_6_month",
#               "recent_1_year", "recent_2_year", "recent_3_year", "this_year", "since_inception", "service_fee"]
#     for field in fields:
#         if getattr(instance, field) in ["", " ", None]:
#             print(getattr(instance, field))
#             print(getattr(instance, "name"))
#             exit()
#             setattr(instance, field, 0.0)


class FundHistory(models.Model):
    """ 基金历史数据 """

    transaction_date = models.DateField(null=True, default=None)  # 交易日期
    unit_net_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)  # 单位净值
    accumulative_net_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)  # 累计净值
    daily_increase_date = models.DecimalField(max_digits=14, decimal_places=2, default=0)  # 日涨幅

    fund = models.ForeignKey(
        Fund,
        related_name='history_data',
        null=True,
        blank=True,
        db_constraint=False,
        on_delete=models.DO_NOTHING,
    )

    class Meta:
        db_table = "fund_history"

    # def calc_income(self):
    #     self.income = float(self.increase_rate) / 100 * float(self.start_money)
    #     self.end_money = float(self.start_money) + float(self.income)
    #     self.save()
    #
    #     return


class Favor(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    name = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=15, blank=True, default=None)

    modified_date = models.DateField(null=True, default=None)
    daily_increase_rate = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = "favors"
        unique_together = ("content_type", "object_id", "code")

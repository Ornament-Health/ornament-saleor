from typing import Optional, Type, TypeVar, Union
from django.conf import settings

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models import Q, Case, When, Value, IntegerField

from saleor.core.utils.json_serializer import CustomJsonEncoder
from saleor.ornament.vendors import VoucherScope
from saleor.channel.models import Channel
from saleor.ornament.geo.models import City
from saleor.order.models import Order


T = TypeVar("T", bound="KDLDiscount")


class KDLDiscountQueryset(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def get_for_order(self, order: Order):
        case_priority = Case(
            When(city__isnull=False, channel__isnull=False, then=Value(2)),
            When(city__isnull=True, channel__isnull=False, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )

        voucher_filter = Q()

        if order.voucher:
            ocl = order.voucher.channel_listings.filter(channel=order.channel).first()
            if ocl:
                voucher_filter = Q(
                    scope=order.voucher.scope,
                    discount_value=ocl.discount_value,
                )

        return (
            self.active()
            .annotate(priority=case_priority)
            .filter(
                voucher_filter | Q(discount_value=0),
                Q(city=order.city, channel=order.channel),
            )
            .order_by("-discount_value", "-priority", "id")
            .first()
        )


class KDLDiscount(models.Model):
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    channel = models.ForeignKey(
        Channel, on_delete=models.SET_NULL, null=True, blank=True
    )

    scope = models.CharField(
        max_length=20, choices=VoucherScope.CHOICES, default=VoucherScope.RETAIL
    )
    is_active = models.BooleanField(default=False)

    email = models.EmailField(blank=True)
    doctor_id = models.CharField(max_length=255, blank=True)
    clinic_id = models.CharField(max_length=255)
    laboratory_id = models.CharField(max_length=255)
    laboratory_name = models.CharField(max_length=255)

    discount_title = models.CharField(max_length=255, null=False, blank=False)
    discount_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )

    meta = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    objects = KDLDiscountQueryset.as_manager()

    class Meta:
        ordering = ("-discount_value", "-channel", "-id")

    def __str__(self):
        return self.discount_title

    @classmethod
    def check_mandatory_order_sku_list(cls, data: Union[dict, list]) -> bool:
        # check if data is dict containing "mandatory_order_sku_list" key
        if isinstance(data, dict):
            if not "mandatory_order_sku_list" in data:
                return False
            data = data["mandatory_order_sku_list"]

        # check data validity (list of 2-length lists)
        if not (
            isinstance(data, list)
            and all(isinstance(i, list) and len(i) == 2 for i in data)
        ):
            return False

        return True

    @classmethod
    def get_mandatory_order_sku_list(cls: Type[T], obj: Optional[T] = None) -> list:
        return (
            obj.meta["mandatory_order_sku_list"]
            if obj and obj.check_mandatory_order_sku_list(obj.meta)
            else settings.KDL_MANDATORY_ORDER_SKU_LIST
        )

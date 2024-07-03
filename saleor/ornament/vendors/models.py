from django.db import models
from django.utils import timezone

from saleor.utils.models import AutoNowUpdateFieldsMixin
from saleor.account.models import User
from saleor.product.models import Category


class VendorDealType(AutoNowUpdateFieldsMixin, models.Model):
    transaction_flow = models.BooleanField(default=False)
    home_visit = models.BooleanField(default=False)
    shipment = models.BooleanField(default=False)
    map_location = models.BooleanField(default=False)
    visit_time = models.BooleanField(default=False)

    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = "ornament_vendor_deal_type"


class Vendor(AutoNowUpdateFieldsMixin, models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    deal_type = models.OneToOneField(
        VendorDealType, null=True, on_delete=models.SET_NULL
    )

    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = "ornament_vendor"

    def __str__(self):
        return self.name


class VendorRule(AutoNowUpdateFieldsMixin, models.Model):
    user = models.ForeignKey(User, related_name="rules", on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

    created = models.DateTimeField(default=timezone.now, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = "ornament_vendor_rule"
        # TODO fix vendor lock for 1+ vendors for the same category
        unique_together = [["user_id", "category_id", "vendor_id"]]

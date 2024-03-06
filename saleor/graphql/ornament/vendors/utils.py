from typing import Optional

from django.conf import settings
from django.core.cache import cache
from django.forms import model_to_dict

from saleor.graphql.ornament.vendors.types import VendorDealType
from saleor.ornament.vendors.models import Vendor


def get_vendor_deal_type(vendor_name: str) -> Optional[VendorDealType]:
    key = f"vendor_deal_type:{vendor_name}"
    cached = cache.get(key)
    ttl = settings.VENDOR_DEAL_TYPE_CACHE_TTL

    if cached:
        if cached == "null":
            return None
        return VendorDealType(**cached)

    vendor = Vendor.objects.filter(name=vendor_name).first()

    if not vendor or not vendor.deal_type:
        cache.set(key, "null", ttl)
        return None

    deal_type_dict = model_to_dict(vendor.deal_type, exclude="id")
    cache.set(key, deal_type_dict, ttl)

    return VendorDealType(**deal_type_dict)

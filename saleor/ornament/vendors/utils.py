import logging
from typing import Optional

from django.conf import settings

from saleor.order.fetch import OrderLineInfo
from saleor.order.models import Order
from saleor.ornament.vendors.kdl import tasks as kdl_tasks
from saleor.ornament.vendors.models import Vendor
from saleor.product.models import ProductVariant

logger = logging.getLogger(__name__)


def apply_kdl_order_logic(order: Order):
    kdl_tasks.place_preorder_via_wsdl.delay(order_id=order.pk)


def apply_kdl_order_notification(order: Order):
    kdl_tasks.send_order_confirmation.delay(order_id=order.pk)


def apply_kdl_vendor_address_augmentation(address_data: dict) -> dict:
    address_data["postal_code"] = settings.DEFAULT_KDL_POSTAL_CODE
    address_data["country_area"] = settings.DEFAULT_KDL_COUNTRY_AREA
    return address_data


def get_vendor_name(vendors: set[str]) -> Optional[str]:
    if len(vendors) < 1:
        logger.error("get_vendor_name: no valid Vendor in order lines")
        return None

    if len(vendors) > 1:
        logger.error("get_vendor_name: found more then 1 valid Vendors in order lines")
        return None

    vendor_name = vendors.pop()

    if Vendor.objects.filter(name=vendor_name).exists():
        return vendor_name

    return None


def apply_vendors_logic(order: Order, order_lines_info: list[OrderLineInfo]) -> None:
    vendors = set([l.variant.name for l in order_lines_info if l.variant])
    vendor_name = get_vendor_name(vendors)

    if vendor_name:
        vendor_logic = vendor_order_logic_map.get(vendor_name)
        if vendor_logic:
            vendor_logic(order)

    return


def apply_vendors_notification(
    order: Order, order_lines_info: list[OrderLineInfo]
) -> None:
    vendors = set([l.variant.name for l in order_lines_info if l.variant])
    vendor_name = get_vendor_name(vendors)

    if vendor_name:
        vendor_notification = vendor_order_notification_map.get(vendor_name)
        if vendor_notification:
            vendor_notification(order)

    return


def apply_vendor_address_augmentation(
    variants: list[ProductVariant], address_data: dict
) -> dict:
    vendors = set([v.name for v in variants])
    vendor_name = get_vendor_name(vendors)

    if vendor_name:
        vendor_address_augmentation = vendor_address_augmentation_map.get(vendor_name)
        if vendor_address_augmentation:
            return vendor_address_augmentation(address_data)

    return address_data


vendor_order_logic_map = {"KDL": apply_kdl_order_logic}
vendor_order_notification_map = {"KDL": apply_kdl_order_notification}
vendor_address_augmentation_map = {"KDL": apply_kdl_vendor_address_augmentation}

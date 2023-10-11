import logging
from typing import Optional

from saleor.order.fetch import OrderLineInfo
from saleor.order.models import Order
from saleor.ornament.vendors.kdl import tasks as kdl_tasks
from saleor.ornament.vendors.models import Vendor

logger = logging.getLogger(__name__)


def apply_kdl_order_logic(order: Order):
    kdl_tasks.place_preorder_via_wsdl.delay(order_id=order.pk)


def apply_kdl_order_notification(order: Order):
    kdl_tasks.send_order_confirmation.delay(order_id=order.pk)


def get_order_vendor_name(order_lines: list[OrderLineInfo]) -> Optional[str]:
    vendors = set([l.variant.name for l in order_lines if l.variant])

    if len(vendors) < 1:
        logger.error("get_order_vendor_name: no valid Vendor in order lines")
        return None

    if len(vendors) > 1:
        logger.error(
            "get_order_vendor_name: found more then 1 valid Vendors in order lines"
        )
        return None

    vendor_name = vendors.pop()

    if Vendor.objects.filter(name=vendor_name).exists():
        return vendor_name

    return None


def apply_vendors_logic(order: Order, order_lines_info: list[OrderLineInfo]) -> None:
    vendor_name = get_order_vendor_name(order_lines_info)

    if vendor_name:
        vendor_logic = vendor_order_logic_map.get(vendor_name)
        if vendor_logic:
            vendor_logic(order)

    return


def apply_vendors_notification(
    order: Order, order_lines_info: list[OrderLineInfo]
) -> None:
    vendor_name = get_order_vendor_name(order_lines_info)

    if vendor_name:
        vendor_notification = vendor_order_notification_map.get(vendor_name)
        if vendor_notification:
            vendor_notification(order)

    return


vendor_order_logic_map = {"KDL": apply_kdl_order_logic}
vendor_order_notification_map = {"KDL": apply_kdl_order_notification}

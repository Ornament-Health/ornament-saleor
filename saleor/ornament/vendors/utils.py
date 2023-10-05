import logging

from saleor.order.fetch import OrderLineInfo
from saleor.order.models import Order
from saleor.ornament.vendors.kdl import tasks as kdl_tasks
from saleor.ornament.vendors.models import Vendor

logger = logging.getLogger(__name__)


def apply_kdl_order_logic(order: Order):
    kdl_tasks.place_preorder_via_wsdl.delay(order_id=order.pk)


def apply_vendors_logic(order: Order, order_lines_info: list[OrderLineInfo]) -> None:
    vendors = set([l.variant.name for l in order_lines_info if l.variant])

    if len(vendors) < 1:
        logger.error("apply_vendors_logic: no valid Vendor in order lines")
        return

    if len(vendors) > 1:
        logger.error(
            "apply_vendors_logic: found more then 1 valid Vendors in order lines"
        )
        return

    vendor_name = vendors.pop()

    if Vendor.objects.filter(name=vendor_name).exists():
        vendor_logic = vendor_order_logic_map.get(vendor_name)

        if vendor_logic:
            vendor_logic(order)

        return


vendor_order_logic_map = {"KDL": apply_kdl_order_logic}

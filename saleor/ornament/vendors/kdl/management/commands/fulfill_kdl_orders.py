import logging

from django.core.management.base import BaseCommand

from saleor.order import models
from saleor.order.actions import create_fulfillments_internal


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fulfill and mark as paid all processed KDL orders"

    def handle(self, *args, **options):
        orders = models.Order.objects.prefetch_related("lines").filter(
            status="unconfirmed", external_lab_order_id__isnull=False
        )
        for order in orders:
            create_fulfillments_internal(order)

from django.apps import AppConfig
from django.db.models.signals import post_save


class OrnamentVendorsConfig(AppConfig):
    name = "saleor.ornament.vendors"

    def ready(self):
        from saleor.order.models import OrderEvent
        from saleor.ornament.utils.signals import order_event_post_save_handler

        post_save.connect(order_event_post_save_handler, sender=OrderEvent)

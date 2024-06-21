from jinja2 import Template

from django.conf import settings

from saleor.celeryconf import app
from saleor.ornament.utils.notification_api import NotificationApi
from saleor.ornament.vendors.kdl.utils import collect_data_for_email


@app.task(autoretry_for=[Exception])
def send_order_confirmation(payload: dict):
    order = payload.get("order") or {}
    subject = f'Ornament order for {float(order.get("total_net_amount", 0))} {order.get("currency")}'
    body = f'Order {order.get("token")} has been created'
    email = order.get("email")

    if email:
        NotificationApi.send_email(recipients=[email], subject=subject, body=body)

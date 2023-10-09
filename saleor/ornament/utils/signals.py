import logging

from django.conf import settings

from saleor.order import OrderEvents
from saleor.order.models import OrderEvent
from saleor.ornament.utils.slack import Slack


logger = logging.getLogger(__name__)


def get_order_event_text(type: str) -> str:
    order_event_type_text = type
    order_event_type_text_choice = [ch for ch in OrderEvents.CHOICES if ch[0] == type]
    if order_event_type_text_choice and order_event_type_text_choice[0]:
        order_event_type_text = order_event_type_text_choice[0][1]
    return order_event_type_text


def order_event_post_save_handler(sender, instance: OrderEvent, created, **kwargs):
    if getattr(instance, "__skip_signals__", False):
        return

    order_event_text = get_order_event_text(instance.type)

    slack_message = {
        "attachments": [
            {
                "color": "#36a64f",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": (
                                f"Order #*{instance.order.id}*. Cобытие в заказе:\n"
                                f"*{order_event_text}"
                                f"{' by ' + str(instance.user.email) if instance.user and instance.user.email else ''}*"
                            ),
                        },
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": (
                                    f"Server *{settings.SLACK_ENVIRONMENT}*, "
                                    f"{instance.date.strftime('%d.%m.%Y %H:%I:%S')}"
                                ),
                            }
                        ],
                    },
                ],
            }
        ]
    }

    Slack.send_message_task.delay(slack_message)

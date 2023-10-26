from enum import Enum
import logging

import requests
from http import HTTPStatus
from django.conf import settings

from saleor.ornament.utils.slack import Slack


logger = logging.getLogger(__name__)


class NotificationDeliveryProviderEnum(Enum):
    EMAIL = "email"
    PUSH = "push"


class NotificationDestinationTypeEnum(Enum):
    SSO_ID = "sso_id"
    EMAIL = "email"
    PUSH = "push"
    FIREBASE_TOKEN = "firebase_token"


class NotificationImportanceTypeEnum(Enum):
    HIGH = "high"
    MIDDLE = "middle"
    LOW = "low"


class NotificationBodyTypeEnum(Enum):
    TEXT = "plain"
    HTML = "html"


class NotificationTextTypeEnum(Enum):
    LONG = "long"
    SHORT = "short"
    SILENT = "silent"


class NotificationApi:
    @staticmethod
    def send_email(
        recipients: list[str],
        subject: str,
        body: str,
    ) -> bool:
        payload = {
            "deliveryProviders": [NotificationDeliveryProviderEnum.EMAIL.value],
            "destination": [
                {"type": NotificationDestinationTypeEnum.EMAIL.value, "value": r}
                for r in recipients
            ],
            "importance": NotificationImportanceTypeEnum.MIDDLE.value,
            "texts": [
                {
                    "type": NotificationTextTypeEnum.LONG.value,
                    "subject": subject,
                    "body": body,
                    "bodySubtype": NotificationBodyTypeEnum.HTML.value,
                    "analyticsLabel": "SALEOR.KDL.ORDER",
                }
            ],
        }

        try:
            response = requests.post(
                settings.ORNAMENT_NOTIFICATION_API_URL,
                json=payload,
            )
            if response.status_code == HTTPStatus.OK:
                return True
            error_message = f"NOTIFICATION API:EXCEPTION: status_code {response.status_code} recipients {recipients}"
            logger.error(error_message)
            slack_message = {"text": error_message}
            Slack.send_message_task.delay(slack_message)
            return False

        except requests.RequestException as e:
            error_message = (
                f"NOTIFICATION API:EXCEPTION: recipients {recipients}, error: {e}"
            )
            logger.error(error_message)
            slack_message = {"text": error_message}
            Slack.send_message_task.delay(slack_message)
            return False

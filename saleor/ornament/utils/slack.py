import logging

from http import HTTPStatus
from django.conf import settings
from requests import RequestException, post

from saleor.celeryconf import app

logger = logging.getLogger(__name__)


class Slack:
    @staticmethod
    @app.task(autoretry_for=[Exception])
    def send_message_task(message: dict) -> None:
        if not settings.SLACK_ENABLED:
            return

        error_message = f"Slack message failed!"

        try:
            response = post(
                settings.SLACK_WEBHOOK,
                json=message,
            )
            if not response.status_code == HTTPStatus.OK:
                logger.error(error_message)

        except (RequestException, Exception) as error:
            logger.error(f"{error_message}, error: {error}")

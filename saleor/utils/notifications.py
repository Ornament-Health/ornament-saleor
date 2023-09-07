from django.conf import settings
from slack_sdk import WebClient, errors

from saleor.celeryconf import app

slack_client = WebClient(token=settings.SLACK_API_TOKEN)


@app.task(autoretry_for=[Exception])
def slack_send_message_task(message: dict) -> None:
    if not settings.SLACK_ENABLED:
        return

    default = {
        "icon_emoji": ":robot_face:",
        "channel": message.get("channel") or settings.SLACK_API_CHANNEL_NAME,
    }
    message = {**default, **message}

    response = slack_client.chat_postMessage(**message)
    if not response["ok"]:
        raise errors.SlackClientError()  # autoretry

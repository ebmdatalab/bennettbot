import json

from flask import request
from slackbot.slackclient import SlackClient

from . import settings
from ..slack import notify_slack


def handle_callback_webhook():
    """Respond to callback webhook.
    """
    print(request.data)
    data = json.loads(request.data.decode())
    client = SlackClient(settings.SLACKBOT_API_TOKEN)
    notify_slack(client, data["channel"], data["message"], data["thread_ts"])

    return ''

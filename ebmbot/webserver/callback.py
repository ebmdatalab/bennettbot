from flask import abort, request
from slackbot.slackclient import SlackClient

from . import settings
from ..slack import notify_slack


def handle_callback_webhook():
    """Respond to callback webhook.
    """
    try:
        channel = request.args["channel"]
        thread_ts = request.args["thread_ts"]
    except KeyError:
        abort(400)

    message = request.data.decode()
    client = SlackClient(settings.SLACKBOT_API_TOKEN)
    notify_slack(client, channel=channel, thread_ts=thread_ts, message=message)

    return ""

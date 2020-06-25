from flask import abort, request
from slackbot.slackclient import SlackClient

from .. import settings
from ..signatures import validate_hmac, InvalidHMAC
from ..slack import notify_slack


def handle_callback_webhook():
    """Respond to callback webhook.
    """
    try:
        channel = request.args["channel"]
        thread_ts = request.args["thread_ts"]
        token = request.args["token"]
    except KeyError:
        abort(400)

    try:
        timestamp, signature = token.split(":", 1)
    except ValueError:
        abort(400)

    try:
        validate_hmac(
            timestamp.encode("utf8"),
            settings.EBMBOT_WEBHOOK_SECRET,
            signature.encode("utf8"),
            max_age=settings.EBMBOT_WEBHOOK_TOKEN_TTL,
        )
    except InvalidHMAC:
        abort(403)

    message = request.data.decode()
    client = SlackClient(settings.SLACKBOT_API_TOKEN)
    notify_slack(client, channel=channel, thread_ts=thread_ts, message=message)

    return ""

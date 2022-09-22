from .logger import logger


def notify_slack(
    slack_client, channel, message_text, thread_ts=None, message_format=None
):
    """Send message to Slack."""
    msg_kwargs = {"text": str(message_text)}
    if message_format == "blocks":
        msg_kwargs["blocks"] = message_text

    logger.info(
        "Sending message", channel=channel, message=message_text, thread_ts=thread_ts
    )
    slack_client.chat_postMessage(channel=channel, thread_ts=thread_ts, **msg_kwargs)

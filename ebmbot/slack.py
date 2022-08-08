from .logger import logger


def notify_slack(slack_client, channel, message_text, thread_ts=None):
    """Send message to Slack."""

    logger.info(
        "Sending message", channel=channel, message=message_text, thread_ts=thread_ts
    )
    slack_client.chat_postMessage(
        channel=channel, text=message_text, thread_ts=thread_ts
    )

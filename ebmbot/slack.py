from .logger import logger


def notify_slack(slack_client, channel, message, thread_ts=None):
    """Send message to Slack."""

    logger.info("Sending message", channel=channel, message=message, thread_ts=thread_ts)
    slack_client.send_message(channel, message, thread_ts=thread_ts)

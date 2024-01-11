from time import sleep

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
    # In case of any unexpected transient exception posting to slack, retry up to 3
    # times and then log the error, to avoid errors in scheduled jobs.
    attempts = 0
    while attempts < 3:
        try:
            resp = slack_client.chat_postMessage(
                channel=channel, thread_ts=thread_ts, **msg_kwargs
            )
            return resp.data
        except Exception as err:
            attempts += 1
            sleep(1)
            error = err

    logger.error(
        "Could not notify slack",
        channel=channel,
        message=message_text,
        thread_ts=thread_ts,
        error=error,
    )

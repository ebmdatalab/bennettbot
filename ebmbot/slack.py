from time import sleep

from .logger import logger


def notify_slack(
    slack_client, channel, message_text, thread_ts=None, message_format=None
):
    """Send message to Slack."""
    msg_kwargs = {"text": str(message_text), "thread_ts": thread_ts, "channel": channel}
    if message_format == "blocks":
        msg_kwargs["blocks"] = message_text

    # Truncate message text to the first charcters
    log_message_text = message_text[:500]
    if len(log_message_text) < len(message_text):
        log_message_text += " (truncated)"

    logger.info(
        "Sending message",
        channel=channel,
        message=log_message_text,
        thread_ts=thread_ts,
    )
    # If messages are longer than 4000 characters, Slack will split them over
    # multiple messages. This breaks code formatting, so if a message with code
    # format is long, we upload it as a file snippet instead
    if message_format == "code":
        if len(message_text) > 3990:
            message_format = "file"
        else:
            msg_kwargs["text"] = f"```{msg_kwargs['text']}```"

    # In case of any unexpected transient exception posting to slack, retry up to 3
    # times and then log the error, to avoid errors in scheduled jobs.
    attempts = 0
    while attempts < 3:
        try:
            if message_format == "file":
                resp = slack_client.files_upload_v2(content=message_text, **msg_kwargs)
            else:
                resp = slack_client.chat_postMessage(**msg_kwargs)
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

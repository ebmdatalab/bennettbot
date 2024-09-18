from time import sleep

from workspace.utils.blocks import get_basic_header_and_text_blocks, truncate_text

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
    # times and then report and log the error, to avoid errors in scheduled jobs.
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
    # The message has failed to post.
    # Modify the Slack message to report the error and try posting it to the channel
    header_text = "Could not notify slack"
    try:
        msg_kwargs["text"] = header_text
        msg_kwargs["blocks"] = get_slack_error_blocks(
            header_text, message_text, error=error
        )
        slack_client.chat_postMessage(**msg_kwargs)
    except Exception:
        # Not even the error message could not be posted to Slack, so
        pass

    finally:
        # Log the error
        logger.error(
            header_text,
            channel=channel,
            message=message_text,
            thread_ts=thread_ts,
            error=error,
        )


def get_slack_error_blocks(header_text, message_text, error):
    error_text = f"```{str(error)}```"
    message_text = f"```{message_text}```"
    return get_basic_header_and_text_blocks(
        header_text=header_text,
        texts=[
            "Slack encountered the error",
            truncate_text(error_text),
            "when trying to post the following message:",
            truncate_text(message_text),
        ],
    )

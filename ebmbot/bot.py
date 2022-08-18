import random
import re
from datetime import datetime, timezone

from slack_bolt import App, BoltResponse
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.error import BoltUnhandledRequestError

from . import job_configs, scheduler, settings
from .logger import log_call, logger


def run():  # pragma: no cover
    """Start the bot running."""
    app = App(
        token=settings.SLACK_BOT_TOKEN,
        signing_secret=settings.SLACK_SIGNING_SECRET,
        # enable @app.error handler to catch the patterns we don't specifically handle
        raise_error_for_unhandled_request=True,
    )
    handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)

    bot_user_id = get_bot_user_id(app.client)
    channels = get_channels(app.client)
    join_all_channels(app.client, channels, bot_user_id)
    register_listeners(app, job_configs.config, channels, bot_user_id)
    handler.start()


def get_bot_user_id(client):
    users = {user["name"]: user["id"] for user in client.users_list()["members"]}
    return users[settings.SLACK_APP_USERNAME]


def get_channels(client):
    return {
        channel["name"]: channel["id"]
        for channel in client.conversations_list(types="public_channel", limit=1000)[
            "channels"
        ]
        if not channel["is_archived"]
    }


def join_all_channels(client, channels, user_id):
    joined = []
    for channel_name, channel_id in channels.items():
        if user_id not in client.conversations_members(channel=channel_id)["members"]:
            logger.info("Bot user joining channel", channel=channel_name)
            client.conversations_join(channel=channel_id, users=user_id)
            joined.append(channel_name)
    return joined


def register_listeners(app, config, channels, bot_user_id):
    """
    Register listeners for this app

    - A single listener for slack requests that mention the bot
    - A single listener for slack requests in DMs with the bot
    - A tech-support listener
    - An error handler
    - A listener for new channels

    The listeners are defined inside this function to allow different config to be
    passed in for tests.
    """

    tech_support_channel_id = channels[settings.SLACK_TECH_SUPPORT_CHANNEL]
    tech_support_regex = re.compile(r".*tech[\s|-]support.*", flags=re.I)

    @app.event(
        "app_mention",
        # Don't match app mentions that include tech support keywords; these will be
        # matched by the tech-support listener
        matchers=[lambda event: not tech_support_regex.match(event["text"])],
    )
    def job_listener(event, say, ack):
        """Respond to every Slack message that mentions the bot (and is not a
        tech-support message) and dispatch to another handler based on the contents
        of the message.

        This allows us to define handlers dynamically based on the job config.
        """
        logger.info(event=event)
        # acknowledge this message to avoid slack retrying in 3s
        ack()
        _listener(event, say)

    @app.message(
        ".*",
        # only match DMs with the bot that are non-tech support messages
        matchers=[
            lambda message: message["channel_type"] == "im"
            and not tech_support_regex.match(message["text"])
        ],
    )
    def im_job_listener(event, say, ack):
        """Respond to every Slack message in a direct message with the bot and dispatch
        to another handler based on the contents of the message.
        """
        # acknowledge this message to avoid slack retrying in 3s
        ack()
        _listener(event, say)

    def _listener(event, say):
        text = event["text"].replace(f"<@{bot_user_id}>", "")

        # handle extra whitespace
        text = " ".join(text.strip().split())
        event["text"] = text
        logger.info("Received message", message=text)

        if text == "status":
            handle_status(event, say)
            return

        for slack_config in config["slack"]:
            if slack_config["regex"].match(text):
                handle_command(app, event, say, slack_config)
                return

        for namespace, help_config in config["help"].items():
            for pattern in [f"^{namespace} help$", f"^help {namespace}$"]:
                if re.match(pattern, text):
                    handle_namespace_help(event, say, help_config)
                    return

        include_apology = text != "help"
        handle_help(event, say, config["help"], include_apology)

    @app.message(
        tech_support_regex,
        # Only match messages posted outside of the tech support channel itself
        matchers=[lambda message: message["channel"] != tech_support_channel_id],
    )
    def repost_to_tech_support(message, say, ack):
        ack()
        # Don't repost messages in DMs with the bot
        if message["channel_type"] in ["channel", "group"]:
            logger.info("Received tech-support message", message=message["text"])
            message_url = app.client.chat_getPermalink(
                channel=message["channel"], message_ts=message["ts"]
            )["permalink"]
            say(message_url, channel=tech_support_channel_id)
        else:
            say(
                "Sorry, I can't call tech-support from this conversation.",
                channel=message["channel"],
            )

    @app.event("channel_created")
    def join_channel(event, ack):
        channel = event["channel"]
        logger.info("Received new channel event", channel=channel["id"])
        ack()
        logger.info("Bot user joining channel", name=channel["name"], id=channel["id"])
        app.client.conversations_join(channel=channel["id"], users=bot_user_id)

    @app.error
    def handle_errors(error):
        if isinstance(error, BoltUnhandledRequestError):
            logger.warn(error)
            return BoltResponse(status=200, body="Unhandled message")
        else:  # pragma: no cover
            # other error patterns
            return BoltResponse(status=500, body="Something went wrong")


@log_call
def handle_status(message, say):
    """Report status of jobs and suppressions back to Slack."""

    status = _build_status()
    say(status, thread_ts=message.get("thread_ts"))


def _build_status():
    running_jobs = []
    scheduled_jobs = []

    for j in scheduler.get_jobs():
        if j["started_at"]:
            running_jobs.append(j)
        else:
            scheduled_jobs.append(j)

    active_suppressions = []
    scheduled_suppressions = []

    for suppression in scheduler.get_suppressions():
        if suppression["start_at"] < str(_now()):
            active_suppressions.append(suppression)
        else:
            scheduled_suppressions.append(suppression)
    lines = [f"The time is {_now()}", ""]

    if running_jobs:
        lines.append(_pluralise(len(running_jobs), "running job:"))
        lines.append("")
        for j in running_jobs:
            lines.append(f"* [{j['id']}] {j['type']} (started at {j['started_at']})")
        lines.append("")

    if scheduled_jobs:
        lines.append(_pluralise(len(scheduled_jobs), "scheduled job:"))
        lines.append("")
        for j in scheduled_jobs:
            lines.append(
                f"* [{j['id']}] {j['type']} (starting after {j['start_after']})"
            )
        lines.append("")

    if active_suppressions:
        lines.append(_pluralise(len(active_suppressions), "active suppression:"))
        lines.append("")
        for s in active_suppressions:
            lines.append(
                f"* [{s['id']}] {s['job_type']} (from {s['start_at']} to {s['end_at']})"
            )
        lines.append("")

    if scheduled_suppressions:
        lines.append(_pluralise(len(scheduled_suppressions), "scheduled suppression:"))
        lines.append("")
        for s in scheduled_suppressions:
            lines.append(
                f"* [{s['id']}] {s['job_type']} (from {s['start_at']} to {s['end_at']})"
            )
        lines.append("")

    if not (
        running_jobs or scheduled_jobs or active_suppressions or scheduled_suppressions
    ):
        lines.append("Nothing is happening")

    return "\n".join(lines).strip()


def _pluralise(n, noun):
    if n == 1:
        return f"There is 1 {noun}"
    else:
        return f"There are {n} {noun}s"


def handle_command(app, message, say, slack_config):
    """Give a thumbs-up to the message, and dispatch to another handler."""
    app.client.reactions_add(
        channel=message["channel"], timestamp=message["ts"], name="crossed_fingers"
    )

    handler = {
        "schedule_job": handle_schedule_job,
        "cancel_job": handle_cancel_job,
        "schedule_suppression": handle_schedule_suppression,
        "cancel_suppression": handle_cancel_suppression,
    }[slack_config["type"]]

    handler(message, say, slack_config)


def _remove_url_formatting(arg):
    """Slack adds `<...>` around URLs. We want to pass them on without the
    formatting.

    """
    if arg.startswith("<http") and arg.endswith(">"):
        arg = arg[1:-1]
    return arg


@log_call
def handle_schedule_job(message, say, slack_config):
    """Schedule a job."""
    match = slack_config["regex"].match(message["text"])
    job_args = dict(zip(slack_config["template_params"], match.groups()))
    deformatted_args = {k: _remove_url_formatting(v) for k, v in job_args.items()}
    scheduler.schedule_job(
        slack_config["job_type"],
        deformatted_args,
        channel=message["channel"],
        thread_ts=message["ts"],
        delay_seconds=slack_config["delay_seconds"],
    )


@log_call
def handle_cancel_job(message, say, slack_config):
    """Cancel a job."""

    scheduler.cancel_job(slack_config["job_type"])


@log_call
def handle_schedule_suppression(message, say, slack_config):
    """Schedule a suppression."""

    match = slack_config["regex"].match(message["text"])
    start_at = _get_datetime(match.groups()[0])
    end_at = _get_datetime(match.groups()[1])

    if start_at is None or end_at is None or start_at >= end_at:
        say(
            "[start_at] and [end_at] must be HH:MM with [start_at] < [end_at]",
            thread_ts=message.get("thread_ts"),
        )
        return

    scheduler.schedule_suppression(slack_config["job_type"], start_at, end_at)


@log_call
def handle_cancel_suppression(message, say, slack_config):
    """Cancel a suppression."""

    scheduler.cancel_suppressions(slack_config["job_type"])


@log_call
def handle_namespace_help(message, say, help_config):
    """Report commands available in namespace."""

    lines = ["The following commands are available:", ""]

    for (command, help_) in help_config:
        lines.append(f"`{command}`: {help_}")

    say("\n".join(lines), thread_ts=message.get("thread_ts"))


@log_call
def handle_help(message, say, help_configs, include_apology):
    """Report all available namespaces."""

    if include_apology:
        lines = ["I'm sorry, I didn't understand you", ""]
    else:
        lines = []
    lines.extend(["Commands in the following namespaces are available:", ""])

    for namespace in sorted(help_configs):
        lines.append(f"* `{namespace}`")

    if message["type"] == "app_mention":
        prefix = f"@{settings.SLACK_APP_USERNAME} "
    else:
        prefix = ""

    lines.append(
        f"Enter `{prefix}[namespace] help` (eg `{prefix}{random.choice(list(help_configs))} help`) for more help"
    )
    say("\n".join(lines), thread_ts=message.get("thread_ts"))


def _get_datetime(hhmm):
    match = re.match(r"^(\d\d):(\d\d)$", hhmm)
    if not match:
        return

    h = int(match.groups()[0])
    if not 0 <= h < 24:
        return

    m = int(match.groups()[1])
    if not 0 <= m < 60:
        return

    today = _now()
    return datetime(today.year, today.month, today.day, h, m, tzinfo=timezone.utc)


def _now():
    return datetime.now(timezone.utc)


if __name__ == "__main__":
    logger.info("running ebmbot.bot")
    run()

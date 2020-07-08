import random
import re
from datetime import datetime, timezone

from slackbot.bot import Bot, respond_to

from . import job_configs, scheduler
from .logger import log_call, logger


def run():  # pragma: no cover
    """Start the slackbot bot running."""

    register_handler(job_configs.config)
    bot = Bot()
    bot.run()


def register_handler(config):
    """Register single handler for responding to Slack messages.

    The handler is defined inside this function to allow different config to be
    passed in for tests.
    """

    @respond_to(".*")
    def handle(message):
        """Respond to every Slack message and dispatch to another handler based
        on the contents of the message.

        This duplicates a little bit of the work that slackbot does, but allows
        us to define handlers dynamically based on the job config.
        """

        text = " ".join(message.body["text"].split())
        logger.info("Received message", message=text)

        if text == "status":
            handle_status(message)
            return

        for slack_config in config["slack"]:
            if slack_config["regex"].match(text):
                handle_command(message, slack_config)
                return

        for namespace, help_config in config["help"].items():
            for pattern in [f"^{namespace} help$", f"^help {namespace}$"]:
                if re.match(pattern, text):
                    handle_namespace_help(message, help_config)
                    return

        include_apology = text != "help"
        handle_help(message, config["help"], include_apology)


@log_call
def handle_status(message):
    """Report status of jobs and suppressions back to Slack."""

    status = _build_status()
    message.reply(status)


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


def handle_command(message, slack_config):
    """Give a thumbs-up to the message, and dispatch to another handler."""

    message.react("+1")

    handler = {
        "schedule_job": handle_schedule_job,
        "cancel_job": handle_cancel_job,
        "schedule_suppression": handle_schedule_suppression,
        "cancel_suppression": handle_cancel_suppression,
    }[slack_config["type"]]

    handler(message, slack_config)


def _remove_url_formatting(arg):
    """Slack adds `<...>` around URLs. We want to pass them on without the
    formatting.

    """
    if arg.startswith("<http") and arg.endswith(">"):
        arg = arg[1:-1]
    return arg


@log_call
def handle_schedule_job(message, slack_config):
    """Schedule a job."""

    match = slack_config["regex"].match(message.body["text"])
    job_args = dict(zip(slack_config["template_params"], match.groups()))
    deformatted_args = {k: _remove_url_formatting(v) for k, v in job_args.items()}
    scheduler.schedule_job(
        slack_config["job_type"],
        deformatted_args,
        channel=message.body["channel"],
        thread_ts=message.thread_ts,
        delay_seconds=slack_config["delay_seconds"],
    )


@log_call
def handle_cancel_job(message, slack_config):
    """Cancel a job."""

    scheduler.cancel_job(slack_config["job_type"])


@log_call
def handle_schedule_suppression(message, slack_config):
    """Schedule a suppression."""

    match = slack_config["regex"].match(message.body["text"])
    start_at = _get_datetime(match.groups()[0])
    end_at = _get_datetime(match.groups()[1])

    if start_at is None or end_at is None or start_at >= end_at:
        message.reply(
            "[start_at] and [end_at] must be HH:MM with [start_at] > [end_at]"
        )
        return

    scheduler.schedule_suppression(slack_config["job_type"], start_at, end_at)


@log_call
def handle_cancel_suppression(message, slack_config):
    """Cancel a suppression."""

    scheduler.cancel_suppressions(slack_config["job_type"])


@log_call
def handle_namespace_help(message, help_config):
    """Report commands available in namespace."""

    lines = ["The following commands are available:", ""]

    for (command, help_) in help_config:
        lines.append(f"`{command}`: {help_}")

    message.reply("\n".join(lines))


@log_call
def handle_help(message, help_configs, include_apology):
    """Report all available namespaces."""

    if include_apology:
        lines = ["I'm sorry, I didn't understand you", ""]
    else:
        lines = []

    lines.extend(["Commands in the following namespaces are available:", ""])

    for namespace in sorted(help_configs):
        lines.append(f"* `{namespace}`")

    lines.append(
        f"Enter `@ebmbot [namespace] help` (eg `@ebmbot {random.choice(list(help_configs))} help`) for more help"
    )

    message.reply("\n".join(lines))


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

import pytest
from slackbot.dispatcher import MessageDispatcher
from slackbot.manager import PluginsManager
from slackbot.slackclient import SlackClient

from ebmbot import bot, scheduler

from .assertions import (
    assert_job_matches,
    assert_slack_client_doesnt_react_to_message,
    assert_slack_client_reacts_to_message,
    assert_slack_client_sends_messages,
    assert_slack_client_sends_no_messages,
    assert_suppression_matches,
)
from .job_configs import config
from .time_helpers import T0, TS, T

# Make sure all tests run when datetime.now() returning T0
pytestmark = pytest.mark.freeze_time(T0)


@pytest.fixture(autouse=True)
def register_handler():
    bot.register_handler(config)


def test_defalut_plugins_not_loaded():
    with assert_slack_client_sends_no_messages():
        handle_message("hey!", category="listen_to", expect_reaction=False)


def test_schedule_job():
    handle_message("test do job 10")

    jj = scheduler.get_jobs_of_type("test_good_job")
    assert len(jj) == 1
    assert_job_matches(jj[0], "test_good_job", {"n": "10"}, "channel", T(60), None)


def test_url_formatting_removed():
    handle_message("test do url <http://www.foo.com>")
    jj = scheduler.get_jobs_of_type("test_job_with_url")
    assert len(jj) == 1
    assert_job_matches(
        jj[0], "test_job_with_url", {"url": "http://www.foo.com"}, "channel", T(0), None
    )


def test_cancel_job():
    handle_message("test do job 10")
    assert scheduler.get_jobs_of_type("test_good_job")

    handle_message("test cancel job")
    assert not scheduler.get_jobs_of_type("test_good_job")


def test_schedule_suppression():
    handle_message("test suppress job from 11:20 to 11:30")

    ss = scheduler.get_suppressions()
    assert len(ss) == 1
    assert_suppression_matches(ss[0], "test_good_job", T(467), T(1067))


def test_schedule_suppression_with_bad_start_at():
    with assert_slack_client_sends_messages(
        websocket=[("channel", "[start_at] and [end_at]")]
    ):
        handle_message("test suppress job from 11:60 to 11:30")

    with assert_slack_client_sends_messages(
        websocket=[("channel", "[start_at] and [end_at]")]
    ):
        handle_message("test suppress job from 24:20 to 11:30")

    with assert_slack_client_sends_messages(
        websocket=[("channel", "[start_at] and [end_at]")]
    ):
        handle_message("test suppress job from xx:20 to 11:30")

    assert not scheduler.get_suppressions()


def test_schedule_suppression_with_bad_end_at():
    with assert_slack_client_sends_messages(
        websocket=[("channel", "[start_at] and [end_at]")]
    ):
        handle_message("test suppress job from 11:20 to 11:60")

    with assert_slack_client_sends_messages(
        websocket=[("channel", "[start_at] and [end_at]")]
    ):
        handle_message("test suppress job from 11:20 to 24:30")

    with assert_slack_client_sends_messages(
        websocket=[("channel", "[start_at] and [end_at]")]
    ):
        handle_message("test suppress job from 11:20 to xx:30")

    assert not scheduler.get_suppressions()


def test_schedule_suppression_with_start_at_after_end_at():
    with assert_slack_client_sends_messages(
        websocket=[("channel", "[start_at] and [end_at]")]
    ):
        handle_message("test suppress job from 11:30 to 11:20")

    with assert_slack_client_sends_messages(
        websocket=[("channel", "[start_at] and [end_at]")]
    ):
        handle_message("test suppress job from 11:20 to 11:20")

    assert not scheduler.get_suppressions()


def test_cancel_suppression():
    handle_message("test suppress job from 11:20 to 11:30")
    assert scheduler.get_suppressions()

    handle_message("test cancel suppression")
    assert not scheduler.get_suppressions()


def test_namespace_help():
    with assert_slack_client_sends_messages(
        websocket=[("channel", "`test do job [n]`: do the job")]
    ):
        handle_message("test help", expect_reaction=False)


def test_help():
    with assert_slack_client_sends_messages(websocket=[("channel", "* `test`")]):
        handle_message("help", expect_reaction=False)


def test_not_understood():
    with assert_slack_client_sends_messages(websocket=[("channel", "I'm sorry")]):
        handle_message("beep boop", expect_reaction=False)


def test_status():
    with assert_slack_client_sends_messages(
        websocket=[("channel", "Nothing is happening")]
    ):
        handle_message("status", expect_reaction=False)


@pytest.mark.parametrize("message", [" test help", "test help ", "test  help"])
def test_message_with_spaces(message):
    with assert_slack_client_sends_messages(
        websocket=[("channel", "`test do job [n]`: do the job")]
    ):
        handle_message(message, expect_reaction=False)


def test_build_status():
    scheduler.schedule_job("good_job", {"k": "v"}, "channel", TS, 0)
    scheduler.schedule_job("odd_job", {"k": "v"}, "channel", TS, 10)
    scheduler.schedule_suppression("odd_job", T(-5), T(5))
    scheduler.schedule_suppression("good_job", T(5), T(15))
    scheduler.reserve_job()

    status = bot._build_status()

    assert (
        status
        == """
The time is 2019-12-10 11:12:13+00:00

There is 1 running job:

* [1] good_job (started at 2019-12-10 11:12:13+00:00)

There is 1 scheduled job:

* [2] odd_job (starting after 2019-12-10 11:12:23+00:00)

There is 1 active suppression:

* [1] odd_job (from 2019-12-10 11:12:08+00:00 to 2019-12-10 11:12:18+00:00)

There is 1 scheduled suppression:

* [2] good_job (from 2019-12-10 11:12:18+00:00 to 2019-12-10 11:12:28+00:00)
""".strip()
    )


def test_pluralise():
    assert bot._pluralise(0, "bot") == "There are 0 bots"
    assert bot._pluralise(1, "bot") == "There is 1 bot"
    assert bot._pluralise(2, "bot") == "There are 2 bots"


def handle_message(text, *, category="respond_to", expect_reaction=True):
    client = SlackClient("api_token", connect=False)
    plugins = PluginsManager()
    plugins.init_plugins()
    dispatcher = MessageDispatcher(client, plugins, None)
    msg = [
        category,
        {"text": text, "channel": "channel", "ts": TS},
    ]

    if expect_reaction:
        with assert_slack_client_reacts_to_message():
            dispatcher.dispatch_msg(msg)
    else:
        with assert_slack_client_doesnt_react_to_message():
            dispatcher.dispatch_msg(msg)

import json
import time

import pytest
from slack_bolt.request import BoltRequest
from slack_sdk.signature import SignatureVerifier

from ebmbot import bot, scheduler

from .assertions import (
    assert_job_matches,
    assert_slack_client_doesnt_react_to_message,
    assert_slack_client_reacts_to_message,
    assert_slack_client_sends_messages,
    assert_suppression_matches,
)
from .job_configs import config
from .time_helpers import T0, TS, T

# Make sure all tests run when datetime.now() returning T0
pytestmark = pytest.mark.freeze_time(T0)


@pytest.fixture(autouse=True)
def register_handler(mock_app):
    app = mock_app.app
    channels = bot.get_channels(app)
    bot_user_id = bot.get_bot_user_id(app)
    bot.register_tech_support_handler(app, channels)
    bot.register_handler(app, config, bot_user_id)
    bot.register_error_handler(app)
    bot.join_all_channels(app, channels, bot_user_id)
    yield


def test_joined_channels(mock_app):
    recorder = mock_app.recorder
    # conversations.members called for each channel (3) (to check if bot is already a
    # member) and conversations.join 2 times to join the channels it's not already in
    assert recorder.mock_received_requests["/conversations.members"] == 3
    assert recorder.mock_received_requests["/conversations.join"] == 2


def test_schedule_job(mock_app):
    handle_message(mock_app, "<@U1234> test do job 10")

    jj = scheduler.get_jobs_of_type("test_good_job")
    assert len(jj) == 1
    assert_job_matches(jj[0], "test_good_job", {"n": "10"}, "channel", T(60), None)


def test_url_formatting_removed(mock_app):
    handle_message(mock_app, "<@U1234> test do url <http://www.foo.com>")
    jj = scheduler.get_jobs_of_type("test_job_with_url")
    assert len(jj) == 1
    assert_job_matches(
        jj[0], "test_job_with_url", {"url": "http://www.foo.com"}, "channel", T(0), None
    )


def test_cancel_job(mock_app):
    handle_message(mock_app, "<@U1234> test do job 10")
    assert scheduler.get_jobs_of_type("test_good_job")

    handle_message(mock_app, "<@U1234> test cancel job", reaction_count=2)
    assert not scheduler.get_jobs_of_type("test_good_job")


def test_schedule_suppression(mock_app):
    handle_message(mock_app, "<@U1234> test suppress job from 11:20 to 11:30")

    ss = scheduler.get_suppressions()
    assert len(ss) == 1
    assert_suppression_matches(ss[0], "test_good_job", T(467), T(1067))


@pytest.mark.parametrize(
    "message_text",
    [
        # bad start_at
        "<@U1234> test suppress job from 11:60 to 11:30",
        "<@U1234> test suppress job from 24:20 to 11:30",
        "<@U1234> test suppress job from xx:20 to 11:30",
        # bad end at
        "<@U1234> test suppress job from 11:20 to 11:60",
        "<@U1234> test suppress job from 11:20 to 24:30",
        "<@U1234> test suppress job from 11:20 to xx:30"
        # start at after end at
        "<@U1234> test suppress job from 11:30 to 11:20",
        # start at equal to end at
        "<@U1234> test suppress job from 11:20 to 11:20",
    ],
)
def test_schedule_suppression_with_bad_times(mock_app, message_text):
    handle_message(mock_app, message_text)
    assert_slack_client_sends_messages(
        mock_app.recorder,
        messages_kwargs=[{"channel": "channel", "text": "[start_at] and [end_at]"}],
    )
    assert not scheduler.get_suppressions()


def test_cancel_suppression(mock_app):
    handle_message(mock_app, "<@U1234> test suppress job from 11:20 to 11:30")
    assert scheduler.get_suppressions()

    handle_message(mock_app, "<@U1234> test cancel suppression", reaction_count=2)
    assert not scheduler.get_suppressions()


def test_namespace_help(mock_app):
    handle_message(mock_app, "<@U1234> test help", reaction_count=0)
    assert_slack_client_sends_messages(
        mock_app.recorder,
        messages_kwargs=[
            {"channel": "channel", "text": "`test do job [n]`: do the job"}
        ],
    )


def test_help(mock_app):
    handle_message(mock_app, "<@U1234> help", reaction_count=0)
    assert_slack_client_sends_messages(
        mock_app.recorder, messages_kwargs=[{"channel": "channel", "text": "* `test`"}]
    )


def test_not_understood(mock_app):
    handle_message(mock_app, "<@U1234> beep boop", reaction_count=0)
    assert_slack_client_sends_messages(
        mock_app.recorder, messages_kwargs=[{"channel": "channel", "text": "I'm sorry"}]
    )


def test_status(mock_app):
    handle_message(mock_app, "<@U1234> status", reaction_count=0)
    assert_slack_client_sends_messages(
        mock_app.recorder,
        messages_kwargs=[{"channel": "channel", "text": "Nothing is happening"}],
    )


@pytest.mark.parametrize("message", [" test help", "test help ", "test  help"])
def test_message_with_spaces(mock_app, message):
    handle_message(mock_app, f"<@U1234>{message}", reaction_count=0)
    assert_slack_client_sends_messages(
        mock_app.recorder,
        messages_kwargs=[
            {"channel": "channel", "text": "`test do job [n]`: do the job"}
        ],
    )


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


@pytest.mark.parametrize(
    "text,channel,respost_expected",
    [
        ("This message should match the tech support listener", "C0002", True),
        # a message posted in the techsupport channel (C0001) does not repost
        ("This message should match the tech support listener", "C0001", False),
        ("This message should match the tech-support listener", "C0003", True),
        ("This message should match the Tech support listener", "C0002", True),
        ("This message should match the tech SUPPORT listener", "C0002", True),
    ],
)
def test_tech_support_listener(mock_app, text, channel, respost_expected):
    # the triggered tech support handler will first fetch the url for the message
    # and then post it to the techsupport channel
    # Before the dispatched message, neither of these paths have been called
    recorder = mock_app.recorder
    tech_support_call_paths = ["/chat.getPermalink", "/chat.postMessage"]
    for path in tech_support_call_paths:
        assert path not in recorder.mock_received_requests

    handle_message(mock_app, text, channel=channel, reaction_count=0)

    # After the dispatched message, each path has been called once
    for path in tech_support_call_paths:
        if respost_expected:
            assert recorder.mock_received_requests[path] == 1
        else:
            assert path not in recorder.mock_received_requests

    if respost_expected:
        # check the contents of the request kwargs for the postMessage
        # posts to the techsupport channel (C0001), with the url retrieved from the
        # mocked getPermalink call (always "http://test")
        assert recorder.mock_received_requests_kwargs["/chat.postMessage"][0] == {
            "text": "http://test",
            "channel": "C0001",
        }


def test_no_listener_found(mock_app):
    # A message must either start with "<@U1234>" (i.e. a user @'d the bot) OR must contain
    # the tech-support pattern
    text = "This message should not match any listener"
    # We use an error handler to deal with unhandled messages, so the resonse status
    # is 200
    resp = handle_message(
        mock_app, text, channel="C0002", reaction_count=0, expected_status=200
    )
    assert_slack_client_sends_messages(mock_app.recorder, messages_kwargs=[])
    assert resp.body == "Unhandled message"


def handle_message(
    mock_app,
    text,
    *,
    type="message",
    reaction_count=1,
    channel="channel",
    expected_status=200,
):
    request = get_mock_request(text, channel)

    resp = mock_app.app.dispatch(request)
    time.sleep(0.1)
    assert resp.status == expected_status

    if reaction_count:
        assert_slack_client_reacts_to_message(mock_app.recorder, reaction_count)
    else:
        assert_slack_client_doesnt_react_to_message(mock_app.recorder)

    return resp


def get_mock_request(text, channel):
    body = {
        "token": "verification_token",
        "team_id": "T111",
        "enterprise_id": "E111",
        "api_app_id": "A111",
        "event": {
            "client_msg_id": "a8744611-0210-4f85-9f15-5faf7fb225c8",
            "type": "message",
            "text": text,
            "user": "W111",
            "ts": "1596183880.004200",
            "team": "T111",
            "channel": channel,
            "event_ts": "1596183880.004200",
            "channel_type": "channel",
        },
        "type": "event_callback",
        "event_id": "Ev111",
        "event_time": 1596183880,
    }
    timestamp, body = str(int(time.time())), json.dumps(body)
    signature = SignatureVerifier("secret").generate_signature(
        body=body,
        timestamp=timestamp,
    )
    headers = {
        "content-type": ["application/json"],
        "x-slack-signature": [signature],
        "x-slack-request-timestamp": [timestamp],
    }
    return BoltRequest(body=body, headers=headers)

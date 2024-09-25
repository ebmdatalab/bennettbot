import json
import os
import shutil
from unittest.mock import Mock, patch

import httpretty
import pytest

from ebmbot import scheduler, settings
from ebmbot.dispatcher import JobDispatcher, MessageChecker, run_once
from ebmbot.slack import slack_web_client

from .assertions import assert_call_counts, assert_slack_client_sends_messages
from .job_configs import config
from .mock_http_request import (
    get_mock_received_requests,
    httpretty_register,
    register_dispatcher_uris,
)
from .time_helpers import T0, TS, T


# Make sure all tests run when datetime.now() returning T0
pytestmark = pytest.mark.freeze_time(T0)


@pytest.fixture(autouse=True)
def remove_logs_dir():
    shutil.rmtree(settings.LOGS_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def mock_http():
    httpretty.enable(allow_net_connect=False)
    register_dispatcher_uris()
    yield
    httpretty.disable()
    httpretty.reset()


def test_run_once():
    scheduler.schedule_suppression("test_good_job", T(-15), T(-5))
    scheduler.schedule_suppression("test_bad_job", T(-15), T(-5))
    scheduler.schedule_suppression("test_really_bad_job", T(-5), T(5))

    scheduler.schedule_job("test_good_job", {}, "channel", TS, 0)
    scheduler.schedule_job("test_bad_job", {}, "channel", TS, 0)
    scheduler.schedule_job("test_really_bad_job", {}, "channel", TS, 0)

    processes = run_once(slack_web_client(), config)

    for p in processes:
        p.join()

    assert os.path.exists(build_log_dir("test_good_job"))
    assert os.path.exists(build_log_dir("test_bad_job"))
    assert not os.path.exists(build_log_dir("test_really_bad_job"))


def test_job_success_with_unsafe_shell_args():
    log_dir = build_log_dir("test_parameterised_job_2")

    scheduler.schedule_job(
        "test_parameterised_job_2", {"thing_to_echo": "<poem>"}, "channel", TS, 0
    )
    job = scheduler.reserve_job()
    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "succeeded"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "<poem>\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success():
    log_dir = build_log_dir("test_good_job")

    scheduler.schedule_job("test_good_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)

    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "succeeded"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_with_parameterised_args():
    log_dir = build_log_dir("test_parameterised_job")

    scheduler.schedule_job("test_parameterised_job", {"path": "poem"}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "succeeded"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_and_report():
    log_dir = build_log_dir("test_reported_job")

    scheduler.schedule_job("test_reported_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "the owl"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_with_no_report():
    log_dir = build_log_dir("test_unreported_job")

    scheduler.schedule_job("test_unreported_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[{"channel": "logs", "text": "about to start"}],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


@patch("ebmbot.dispatcher.settings.MAX_SLACK_NOTIFY_RETRIES", 0)
def test_job_success_with_slack_exception():
    # Test that the job still succeeds even if notifying slack errors
    # We mock the MAX_SLACK_NOTIFY_RETRIES so that this test doesn't do the
    # (time-consuming) retrying in slack.py
    httpretty_register(
        {"chat.postMessage": [{"ok": False, "error": "error"}]},
    )

    log_dir = build_log_dir("test_good_job")

    scheduler.schedule_job("test_good_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    client = slack_web_client()
    # confirm that posting a message with the client raises an error
    with pytest.raises(Exception):
        client.chat_postMessage(text="test", channel="channel")

    do_job(client, job)

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_failure():
    log_dir = build_log_dir("test_bad_job")

    scheduler.schedule_job("test_bad_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()
    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "failed"},
            # failed message url reposted to tech support channel
            {
                "channel": settings.SLACK_TECH_SUPPORT_CHANNEL,
                "text": "http://example.com",
            },
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == "cat: no-poem: No such file or directory\n"


def test_job_failure_in_dm():
    log_dir = build_log_dir("test_bad_job")

    scheduler.schedule_job("test_bad_job", {}, "IM0001", TS, 0, is_im=True)
    job = scheduler.reserve_job()
    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        # NOTE: NOT reposted to tech support from a DM with the bot
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "IM0001", "text": "failed"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == "cat: no-poem: No such file or directory\n"


def test_job_failure_when_command_not_found():
    log_dir = build_log_dir("test_really_bad_job")

    scheduler.schedule_job("test_really_bad_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": f"failed.\nFind logs in {log_dir}"},
            # failed message url reposted to tech support channel
            {
                "channel": settings.SLACK_TECH_SUPPORT_CHANNEL,
                "text": "http://example.com",
            },
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == "/bin/sh: 1: dog: not found\n"


@patch("ebmbot.settings.HOST_LOGS_DIR", "/host/logs/")
def test_job_failure_with_host_log_dirs_setting():
    log_dir = build_log_dir("test_bad_job")

    scheduler.schedule_job("test_bad_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()
    do_job(slack_web_client(), job)

    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "failed.\nFind logs in /host/logs/"},
            # failed message url reposted to tech support channel
            {
                "channel": settings.SLACK_TECH_SUPPORT_CHANNEL,
                "text": "http://example.com",
            },
        ],
    )

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == "cat: no-poem: No such file or directory\n"


def test_python_job_success():
    log_dir = build_log_dir("test_good_python_job")

    scheduler.schedule_job("test_good_python_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "Hello World!\n"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "Hello World!\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_python_job_success_with_parameterised_args():
    log_dir = build_log_dir("test_parameterised_python_job")

    scheduler.schedule_job(
        "test_parameterised_python_job", {"name": "Fred"}, "channel", TS, 0
    )
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "Hello Fred!\n"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "Hello Fred!\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_python_job_success_with_blocks():
    log_dir = build_log_dir("test_good_python_job_with_blocks")

    scheduler.schedule_job("test_good_python_job_with_blocks", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)
    expected_blocks = [
        {"type": "section", "text": {"type": "plain_text", "text": "Hello World!"}}
    ]

    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {
                "channel": "channel",
                "text": "{'type': 'plain_text', 'text': 'Hello World!'}",
                "blocks": expected_blocks,
            },
        ],
        message_format="blocks",
    )
    with open(os.path.join(log_dir, "stdout")) as f:
        assert json.load(f) == expected_blocks

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_python_job_failure_with_blocks():
    log_dir = build_log_dir("test_bad_python_job_with_blocks")

    scheduler.schedule_job("test_bad_python_job_with_blocks", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)

    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "failed"},
            # failed message url reposted to tech support channel
            {
                "channel": settings.SLACK_TECH_SUPPORT_CHANNEL,
                "text": "http://example.com",
            },
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        stderr = f.read()
        assert "Traceback (most recent call last):" in stderr
        assert "An error was found!" in stderr


def test_python_job_failure():
    log_dir = build_log_dir("test_bad_python_job")

    scheduler.schedule_job("test_bad_python_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()
    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "failed"},
            # failed message url reposted to tech support channel
            {
                "channel": settings.SLACK_TECH_SUPPORT_CHANNEL,
                "text": "http://example.com",
            },
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        stderr = f.read()
        assert "No such file or directory" in stderr


def test_python_job_with_no_output():
    log_dir = build_log_dir("test_python_job_no_output")

    scheduler.schedule_job("test_python_job_no_output", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "No output found for command"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_config_with_no_python_file():
    log_dir = build_log_dir("test1_good_job")

    scheduler.schedule_job("test1_good_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "succeeded"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_with_code_format():
    scheduler.schedule_job("test_good_job_with_code", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)

    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {
                "channel": "channel",
                "text": "```the owl and the pussycat\n```",
            },
        ],
        message_format="code",
    )


def test_job_with_long_code_output_is_uploaded_as_file():
    httpretty_register(
        {
            "files.getUploadURLExternal": [
                {
                    "ok": True,
                    "upload_url": "https://files.example.com/upload/v1/ABC123",
                    "file_id": "F123ABC456",
                }
            ],
            "files.completeUploadExternal": [
                {"ok": True, "files": [{"id": "F123ABC456", "title": "test"}]}
            ],
        }
    )
    httpretty.register_uri(
        httpretty.POST,
        "https://files.example.com/upload/v1/ABC123",
    )

    scheduler.schedule_job("test_python_job_long_code_output", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(slack_web_client(), job)

    assert_call_counts(
        {
            "/api/chat.postMessage": 1,
            "/api/files.getUploadURLExternal": 1,
            "/upload/v1/ABC123": 1,
            "/api/files.completeUploadExternal": 1,
        }
    )
    assert_slack_client_sends_messages(
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
        ],
    )


def do_job(client, job):
    job_dispatcher = JobDispatcher(client, job, config)
    job_dispatcher.do_job()


def build_log_dir(job_type_with_namespace):
    return os.path.join(
        settings.LOGS_DIR, job_type_with_namespace, T0.strftime("%Y%m%d-%H%M%S")
    )


def test_message_checker_config():
    checker = MessageChecker(slack_web_client("bot"), slack_web_client("user"))
    # channel IDs are retrieved from mock_web_api_server
    assert checker.config == {
        "tech-support": {
            "reaction": "sos",
            "channel": settings.SLACK_TECH_SUPPORT_CHANNEL,
        },
        "bennett-admins": {
            "reaction": "flamingo",
            "channel": settings.SLACK_BENNETT_ADMINS_CHANNEL,
        },
    }


def test_message_checker_run():
    httpretty_register(
        {
            "search.messages": [
                {"ok": True, "messages": {"matches": []}},
            ]
        }
    )

    checker = MessageChecker(slack_web_client("bot"), slack_web_client("user"))

    # Mock the run function so the checker runs twice, not forever
    run_fn = Mock(side_effect=[True, True, False])
    checker.do_check(run_fn, delay=0.1)

    # search.messages is called twice for each run of the checker
    # no matches, so no reactions or messages reposted.
    assert len(httpretty.latest_requests()) == 4


@pytest.mark.parametrize(
    "keyword,support_channel,reaction",
    (
        ["tech-support", settings.SLACK_TECH_SUPPORT_CHANNEL, "sos"],
        ["bennett-admins", settings.SLACK_BENNETT_ADMINS_CHANNEL, "flamingo"],
    ),
)
def test_message_checker_tech_support_messages(keyword, support_channel, reaction):
    httpretty_register(
        {
            "search.messages": [
                {
                    "ok": True,
                    "messages": {
                        "matches": [
                            {
                                "text": f"Calling {keyword}",
                                "channel": {"id": "C4444"},
                                "ts": "1709460000.0",
                            },
                            {
                                "text": "This is a forwarded message",
                                "channel": {"id": "C4444"},
                                "ts": "1709000000.0",
                            },
                        ],
                    },
                }
            ],
            "reactions.add": [{"ok": True}],
        }
    )

    checker = MessageChecker(slack_web_client("bot"), slack_web_client("user"))

    checker.check_messages(keyword, "2024-03-04", "2024-03-02")
    # search.messages is called once
    # other endpoints called once each for one matched message requiring
    # reaction and reposting.
    assert len(httpretty.latest_requests()) == 4

    requests_by_path = get_mock_received_requests()
    assert requests_by_path["/api/search.messages"] == [
        {
            "query": [
                f"{keyword} -has::{reaction}: -in:#{support_channel} "
                f"-from:@{settings.SLACK_APP_USERNAME} -is:dm "
                "before:2024-03-04 after:2024-03-02"
            ]
        }
    ]
    # fetch the permalink for the message with ts matching the message to be reposted
    assert requests_by_path["/api/chat.getPermalink"] == [
        {
            "channel": ["C4444"],
            "message_ts": ["1709460000.0"],
        }
    ]
    # reposted to correct channel
    assert requests_by_path["/api/chat.postMessage"][0] == {
        "channel": support_channel,
        "text": "http://example.com",
    }

    # reacted with correct emoji
    assert requests_by_path["/api/reactions.add"] == [
        {
            "channel": ["C4444"],
            "name": [reaction],
            "timestamp": ["1709460000.0"],
        }
    ]

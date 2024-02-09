import json
import os
import shutil
from unittest.mock import patch

import pytest

from ebmbot import scheduler, settings
from ebmbot.dispatcher import JobDispatcher, run_once

from .assertions import assert_slack_client_sends_messages
from .job_configs import config
from .time_helpers import T0, TS, T


# Make sure all tests run when datetime.now() returning T0
pytestmark = pytest.mark.freeze_time(T0)


@pytest.fixture(autouse=True)
def remove_logs_dir():
    shutil.rmtree(settings.LOGS_DIR, ignore_errors=True)


def test_run_once(mock_client):
    # Because this mock gets used in a subprocess (I think) we can't actually
    # get any information out of it about how it was used.
    slack_client = mock_client.client

    scheduler.schedule_suppression("test_good_job", T(-15), T(-5))
    scheduler.schedule_suppression("test_bad_job", T(-15), T(-5))
    scheduler.schedule_suppression("test_really_bad_job", T(-5), T(5))

    scheduler.schedule_job("test_good_job", {}, "channel", TS, 0)
    scheduler.schedule_job("test_bad_job", {}, "channel", TS, 0)
    scheduler.schedule_job("test_really_bad_job", {}, "channel", TS, 0)

    processes = run_once(slack_client, config)

    for p in processes:
        p.join()

    assert os.path.exists(build_log_dir("test_good_job"))
    assert os.path.exists(build_log_dir("test_bad_job"))
    assert not os.path.exists(build_log_dir("test_really_bad_job"))


def test_job_success_with_unsafe_shell_args(mock_client):
    log_dir = build_log_dir("test_paramaterised_job_2")

    scheduler.schedule_job(
        "test_paramaterised_job_2", {"thing_to_echo": "<poem>"}, "channel", TS, 0
    )
    job = scheduler.reserve_job()
    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "succeeded"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "<poem>\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success(mock_client):
    log_dir = build_log_dir("test_good_job")

    scheduler.schedule_job("test_good_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "succeeded"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_with_parameterised_args(mock_client):
    log_dir = build_log_dir("test_paramaterised_job")

    scheduler.schedule_job("test_paramaterised_job", {"path": "poem"}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "succeeded"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_and_report(mock_client):
    log_dir = build_log_dir("test_reported_job")

    scheduler.schedule_job("test_reported_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "the owl"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_with_no_report(mock_client):
    log_dir = build_log_dir("test_unreported_job")

    scheduler.schedule_job("test_unreported_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[{"channel": "logs", "text": "about to start"}],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_with_slack_exception(mock_client_with_slack_exception):
    # Test that the job still succeeds even if notifying slack errors
    log_dir = build_log_dir("test_good_job")

    scheduler.schedule_job("test_good_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client_with_slack_exception.client, job)
    assert_slack_client_sends_messages(
        mock_client_with_slack_exception.recorder,
        messages_kwargs=[],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_failure(mock_client):
    log_dir = build_log_dir("test_bad_job")

    scheduler.schedule_job("test_bad_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()
    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "failed"},
            # failed message url reposted to tech support channel (C0001 in the mock)
            {"channel": "C0001", "text": "http://test"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == "cat: no-poem: No such file or directory\n"


def test_job_failure_in_dm(mock_client):
    log_dir = build_log_dir("test_bad_job")

    scheduler.schedule_job("test_bad_job", {}, "IM0001", TS, 0, is_im=True)
    job = scheduler.reserve_job()
    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
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


def test_job_failure_when_command_not_found(mock_client):
    log_dir = build_log_dir("test_really_bad_job")

    scheduler.schedule_job("test_really_bad_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": f"failed.\nFind logs in {log_dir}"},
            # failed message url reposted to tech support channel (C0001 in the mock)
            {"channel": "C0001", "text": "http://test"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == "/bin/sh: 1: dog: not found\n"


@patch("ebmbot.settings.HOST_LOGS_DIR", "/host/logs/")
def test_job_failure_with_host_log_dirs_setting(mock_client):
    log_dir = build_log_dir("test_bad_job")

    scheduler.schedule_job("test_bad_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()
    do_job(mock_client.client, job)

    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "failed.\nFind logs in /host/logs/"},
            # failed message url reposted to tech support channel (C0001 in the mock)
            {"channel": "C0001", "text": "http://test"},
        ],
    )

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == "cat: no-poem: No such file or directory\n"


def test_python_job_success(mock_client):
    log_dir = build_log_dir("test_good_python_job")

    scheduler.schedule_job("test_good_python_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "Hello World!\n"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "Hello World!\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_python_job_success_with_parameterised_args(mock_client):
    log_dir = build_log_dir("test_parameterised_python_job")

    scheduler.schedule_job(
        "test_parameterised_python_job", {"name": "Fred"}, "channel", TS, 0
    )
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "Hello Fred!\n"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "Hello Fred!\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_python_job_success_with_blocks(mock_client):
    log_dir = build_log_dir("test_good_python_job_with_blocks")

    scheduler.schedule_job("test_good_python_job_with_blocks", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    expected_blocks = [
        {"type": "section", "text": {"type": "plain_text", "text": "Hello World!"}}
    ]

    assert_slack_client_sends_messages(
        mock_client.recorder,
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


def test_python_job_failure_with_blocks(mock_client):
    log_dir = build_log_dir("test_bad_python_job_with_blocks")

    scheduler.schedule_job("test_bad_python_job_with_blocks", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)

    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "failed"},
            # failed message url reposted to tech support channel (C0001 in the mock)
            {"channel": "C0001", "text": "http://test"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        stderr = f.read()
        assert "Traceback (most recent call last):" in stderr
        assert "An error was found!" in stderr


def test_python_job_failure(mock_client):
    log_dir = build_log_dir("test_bad_python_job")

    scheduler.schedule_job("test_bad_python_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()
    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "failed"},
            # failed message url reposted to tech support channel (C0001 in the mock)
            {"channel": "C0001", "text": "http://test"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        stderr = f.read()
        assert "No such file or directory" in stderr


def test_python_job_with_no_output(mock_client):
    log_dir = build_log_dir("test_python_job_no_output")

    scheduler.schedule_job("test_python_job_no_output", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "No output found for command"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == ""

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_success_config_with_no_python_file(mock_client):
    log_dir = build_log_dir("test1_good_job")

    scheduler.schedule_job("test1_good_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "succeeded"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "the owl and the pussycat\n"

    with open(os.path.join(log_dir, "stderr")) as f:
        assert f.read() == ""


def test_job_with_code_format(mock_client):
    scheduler.schedule_job("test_good_job_with_code", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)

    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {
                "channel": "channel",
                "text": "```the owl and the pussycat\n```",
            },
        ],
        message_format="code",
    )


def test_job_with_long_code_output_is_uploaded_as_file(mock_client):
    scheduler.schedule_job("test_python_job_long_code_output", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)

    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
        ],
        message_format="file",
    )


def do_job(client, job):
    job_dispatcher = JobDispatcher(client, job, config)
    job_dispatcher.do_job()


def build_log_dir(job_type_with_namespace):
    return os.path.join(
        settings.LOGS_DIR, job_type_with_namespace, T0.strftime("%Y%m%d-%H%M%S")
    )

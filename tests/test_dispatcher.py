import json
import os
import shutil

import pytest

from ebmbot import scheduler, settings, webserver
from ebmbot.dispatcher import JobDispatcher, run_once

from .assertions import (
    assert_patched_slack_client_sends_messages,
    assert_slack_client_sends_messages,
)
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


def test_job_failure_when_command_not_found(mock_client):
    log_dir = build_log_dir("test_really_bad_job")

    scheduler.schedule_job("test_really_bad_job", {}, "channel", TS, 0)
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
        assert f.read() == "/bin/sh: 1: dog: not found\n"


def test_job_with_callback(mock_client):
    log_dir = build_log_dir("test_job_to_test_callback")

    scheduler.schedule_job("test_job_to_test_callback", {}, "channel", TS, 0)
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
        url = f.read().strip()

    client = webserver.app.test_client()

    with assert_patched_slack_client_sends_messages(
        messages_kwargs=[{"channel": "channel", "text": "Job done", "thread_ts": TS}]
    ):
        rsp = client.post(url, data='{"message": "Job done"}')
        assert rsp.status_code == 200


def test_python_job_success(mock_client):
    log_dir = build_log_dir("test_good_python_job")

    scheduler.schedule_job("test_good_python_job", {}, "channel", TS, 0)
    job = scheduler.reserve_job()

    do_job(mock_client.client, job)
    assert_slack_client_sends_messages(
        mock_client.recorder,
        messages_kwargs=[
            {"channel": "logs", "text": "about to start"},
            {"channel": "channel", "text": "Hello World!"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "Hello World!"

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
            {"channel": "channel", "text": "Hello Fred!"},
        ],
    )

    with open(os.path.join(log_dir, "stdout")) as f:
        assert f.read() == "Hello Fred!"

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
        assert "Traceback (most recent call last):" in stderr
        assert "module 'jobs' has no attribute 'unknown'" in stderr


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


def do_job(client, job):
    job_dispatcher = JobDispatcher(client, job, config)
    job_dispatcher.do_job()


def build_log_dir(job_type_with_namespace):
    return os.path.join(
        settings.LOGS_DIR, job_type_with_namespace, T0.strftime("%Y%m%d-%H%M%S")
    )

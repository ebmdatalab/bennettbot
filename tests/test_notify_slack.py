from unittest.mock import patch

import httpretty
from slack_sdk import WebClient

from ebmbot.slack import notify_slack
from workspace.utils.blocks import get_text_block

from .mock_http_request import get_mock_received_requests, httpretty_register


@httpretty.activate(allow_net_connect=False)
def test_notify_slack_success():
    httpretty_register(
        {"chat.postMessage": [{"ok": True, "ts": 123.45, "channel": "test-channel"}]}
    )

    notify_slack(WebClient(), "test-channel", "my message", 234.56)
    latest_requests = get_mock_received_requests()["/api/chat.postMessage"]
    assert len(latest_requests) == 1
    assert latest_requests[0] == {
        "channel": "test-channel",
        "thread_ts": 234.56,
        "text": "my message",
    }


@httpretty.activate(allow_net_connect=False)
def test_notify_slack_success_blocks():
    httpretty_register(
        {"chat.postMessage": [{"ok": True, "ts": 123.45, "channel": "test-channel"}]}
    )
    block_message = [get_text_block(text="my message")]
    notify_slack(
        WebClient(), "test-channel", block_message, 234.56, message_format="blocks"
    )
    latest_requests = get_mock_received_requests()["/api/chat.postMessage"]
    assert len(latest_requests) == 1
    assert latest_requests[0] == {
        "channel": "test-channel",
        "thread_ts": 234.56,
        "text": str(block_message),
        "blocks": block_message,
    }


@httpretty.activate(allow_net_connect=False)
@patch("ebmbot.dispatcher.settings.MAX_SLACK_NOTIFY_RETRIES", 1)
def test_notify_slack_retries():
    # Mock 2 responses from the postMessage endpoint
    # We allow 1 retry to notify slack with the original message
    # The first attempt is an error, the second succeeds
    httpretty_register(
        {"chat.postMessage": [{"ok": False, "error": "error"}, {"ok": True}]}
    )

    notify_slack(WebClient(), "test-channel", "my message", 234.56, retry_delay=0.1)
    latest_requests = get_mock_received_requests()["/api/chat.postMessage"]
    assert len(latest_requests) == 2
    # both attempted calls are with the original message (first errors, second succeeds)
    for request_body in latest_requests:
        assert request_body == {
            "channel": "test-channel",
            "thread_ts": 234.56,
            "text": "my message",
        }


@httpretty.activate(allow_net_connect=False)
@patch("ebmbot.dispatcher.settings.MAX_SLACK_NOTIFY_RETRIES", 0)
def test_notify_slack_retries_fallback():
    # Mock 2 responses from the postMessage endpoint
    # We only allow 1 atttempt to notify slack with the original message
    # The first attempt is an error, so we fall back to notifying about the failure
    # The fallback (second mocked response) succeeds
    httpretty_register(
        {"chat.postMessage": [{"ok": False, "error": "error"}, {"ok": True}]}
    )

    notify_slack(WebClient(), "test-channel", "my message", 234.56, retry_delay=0.1)
    latest_requests = get_mock_received_requests()["/api/chat.postMessage"]
    assert len(latest_requests) == 2

    # first attempted call with original message
    assert latest_requests[0] == {
        "channel": "test-channel",
        "thread_ts": 234.56,
        "text": "my message",
    }
    # second (successful) call with failure message
    assert latest_requests[1]["text"] == "Could not notify slack"


@httpretty.activate(allow_net_connect=False)
@patch("ebmbot.dispatcher.settings.MAX_SLACK_NOTIFY_RETRIES", 1)
def test_notify_slack_retries_fallback_error():
    # Make the postMessage endpoint always error
    # We only allow 2 atttempt to notify slack with the original message
    # Both error, so we fall back to notifying about the failure
    # The fallback (second mocked response) also errors, so we give up and just log
    httpretty_register({"chat.postMessage": [{"ok": False, "error": "error"}]})

    notify_slack(WebClient(), "test-channel", "my message", 234.56, retry_delay=0.1)
    latest_requests = get_mock_received_requests()["/api/chat.postMessage"]
    assert len(latest_requests) == 3

    assert len(httpretty.latest_requests()) == 3
    for request_body in latest_requests[:2]:
        # first attempted calls with original message
        assert request_body == {
            "channel": "test-channel",
            "thread_ts": 234.56,
            "text": "my message",
        }
    # 3rd call with failure message also errors
    assert latest_requests[2]["text"] == "Could not notify slack"

import json

import pytest

from ebmbot import webserver

from ..assertions import assert_slack_client_sends_messages


@pytest.fixture()
def web_client():
    return webserver.app.test_client()


def test_with_valid_payload(web_client):
    payload = {
        "channel": "channel",
        "message": "Job done",
        "thread_ts": "1234567890.098765",
    }
    with assert_slack_client_sends_messages(
        web_api=[("channel", "Job done", "1234567890.098765")]
    ):
        rsp = web_client.post("/callback/", data=json.dumps(payload))
    assert rsp.status_code == 200

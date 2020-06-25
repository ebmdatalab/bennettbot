import pytest

from ebmbot import webserver

from ..assertions import assert_slack_client_sends_messages


@pytest.fixture()
def web_client():
    return webserver.app.test_client()


def test_with_valid_payload(web_client):
    with assert_slack_client_sends_messages(
        web_api=[("channel", "Job done", "1234567890.098765")]
    ):
        rsp = web_client.post(
            "/callback/?channel=channel&thread_ts=1234567890.098765", data="Job done"
        )
    assert rsp.status_code == 200

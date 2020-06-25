import pytest

from ebmbot import webserver

from ..assertions import assert_slack_client_sends_messages
from ..time_helpers import T


pytestmark = pytest.mark.freeze_time(T(10))


@pytest.fixture()
def web_client():
    return webserver.app.test_client()


def test_with_valid_payload(web_client):
    url = "/callback/?channel=channel&thread_ts=1234567890.098765&token=1575976333.0:43dfc12afbe479453b7ad54bbca9250923d80d51"

    with assert_slack_client_sends_messages(
        web_api=[("channel", "Job done", "1234567890.098765")]
    ):
        rsp = web_client.post(url, data="Job done",)
        assert rsp.status_code == 200


@pytest.mark.parametrize(
    "url",
    [
        "/callback/?thread_ts=1234567890.098765&token=1575976333.0:43dfc12afbe479453b7ad54bbca9250923d80d51",  # missing channel
        "/callback/?channel=channel&token=1575976333.0:43dfc12afbe479453b7ad54bbca9250923d80d51",  # missing thread_ts
        "/callback/?channel=channel&thread_ts=1234567890.098765&",  # missing token
        "/callback/?channel=channel&thread_ts=1234567890.098765&token=1575976333.0",  # invalid token
    ],
)
def test_with_invalid_payload(web_client, url):
    with assert_slack_client_sends_messages(web_api=[]):
        rsp = web_client.post(url, data="Job done",)
        assert rsp.status_code == 400


@pytest.mark.parametrize(
    "url",
    [
        "/callback/?channel=channel&thread_ts=1234567890.098765&token=1575976333.1:43dfc12afbe479453b7ad54bbca9250923d80d51",  # invalid signature
        "/callback/?channel=channel&thread_ts=1234567890.098765&token=1575976333.0:43dfc12afbe479453b7ad54bbca9250923d80d51",  # expired token
    ],
)
def test_unauthorised(freezer, web_client, url):
    freezer.move_to(T(60 * 60 + 1))
    with assert_slack_client_sends_messages(web_api=[]):
        rsp = web_client.post(url, data="Job done",)
        assert rsp.status_code == 403

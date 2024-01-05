from unittest.mock import patch

import pytest

from ebmbot import scheduler

from ..assertions import assert_job_matches
from ..time_helpers import T0, T


# Make sure all tests run when datetime.now() returning T0
pytestmark = pytest.mark.freeze_time(T0)


PAYLOAD_PR_CLOSED = '{"action": "closed", "pull_request": {"merged": true}}'
PAYLOAD_PR_CLOSED_UNMERGED = '{"action": "closed", "pull_request": {"merged": false}}'
PAYLOAD_PR_OPENED = '{"action": "opened", "pull_request": {}}'
PAYLOAD_ISSUE_OPENED = '{"action": "opened", "issue": {}}'


dummy_config = {"jobs": {"test_deploy": {}}}


def test_no_auth_header(web_client):
    rsp = web_client.post("/github/test/", data=PAYLOAD_PR_CLOSED)
    assert rsp.status_code == 403


def test_malformed_auth_header(web_client):
    headers = {"X-Hub-Signature": "abcdef"}
    rsp = web_client.post("/github/test/", data=PAYLOAD_PR_CLOSED, headers=headers)
    assert rsp.status_code == 403


def test_invalid_auth_header(web_client):
    headers = {"X-Hub-Signature": "sha1=abcdef"}
    rsp = web_client.post("/github/test/", data=PAYLOAD_PR_CLOSED, headers=headers)
    assert rsp.status_code == 403


def test_valid_auth_header(web_client):
    headers = {"X-Hub-Signature": "sha1=3e09e676b4a62b634401b44b4c4ff1f58404e746"}

    with patch("ebmbot.webserver.github.config", new=dummy_config):
        rsp = web_client.post("/github/test/", data=PAYLOAD_PR_CLOSED, headers=headers)

    assert rsp.status_code == 200


def test_on_closed_merged_pr(web_client):
    headers = {"X-Hub-Signature": "sha1=3e09e676b4a62b634401b44b4c4ff1f58404e746"}

    with patch("ebmbot.webserver.github.config", new=dummy_config):
        rsp = web_client.post("/github/test/", data=PAYLOAD_PR_CLOSED, headers=headers)

    assert rsp.status_code == 200
    jj = scheduler.get_jobs_of_type("test_deploy")
    assert len(jj) == 1
    assert_job_matches(jj[0], "test_deploy", {}, "#general", T(60), None)


def test_on_closed_unmerged_pr(web_client):
    headers = {"X-Hub-Signature": "sha1=9bd6f75640ef7a6c1a573cf5d423be7d8ed23c3b"}
    rsp = web_client.post(
        "/github/test/", data=PAYLOAD_PR_CLOSED_UNMERGED, headers=headers
    )
    assert rsp.status_code == 200
    assert not scheduler.get_jobs_of_type("test_deploy")


def test_on_opened_pr(web_client):
    headers = {"X-Hub-Signature": "sha1=4cc85e5c6e7a1f3a03aeaef924f1cfa7a3d72384"}
    rsp = web_client.post("/github/test/", data=PAYLOAD_PR_OPENED, headers=headers)
    assert rsp.status_code == 200
    assert not scheduler.get_jobs_of_type("test_deploy")


def test_on_opened_issue(web_client):
    headers = {"X-Hub-Signature": "sha1=6e6218f3e729aca3abce2644128a1d29af2c76ab"}
    rsp = web_client.post("/github/test/", data=PAYLOAD_ISSUE_OPENED, headers=headers)
    assert rsp.status_code == 200
    assert not scheduler.get_jobs_of_type("test_deploy")


def test_unknown_project(web_client):
    headers = {"X-Hub-Signature": "sha1=3e09e676b4a62b634401b44b4c4ff1f58404e746"}
    rsp = web_client.post(
        "/github/another-name/", data=PAYLOAD_PR_CLOSED, headers=headers
    )
    assert rsp.status_code == 400
    assert rsp.data == b"Unknown project: another-name"

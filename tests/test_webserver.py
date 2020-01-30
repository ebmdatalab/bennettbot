import pytest

from ebmbot import scheduler, webserver


@pytest.fixture()
def web_client():
    return webserver.app.test_client()


PAYLOAD_PR_CLOSED = '{"action": "closed", "pull_request": {"merged": true}}'
PAYLOAD_PR_CLOSED_UNMERGED = '{"action": "closed", "pull_request": {"merged": false}}'
PAYLOAD_PR_OPENED = '{"action": "opened", "pull_request": {}}'
PAYLOAD_ISSUE_OPENED = '{"action": "opened", "issue": {}}'


def test_no_auth_header(web_client):
    rsp = web_client.post("/github/", data=PAYLOAD_PR_CLOSED)
    assert rsp.status_code == 403


def test_malformed_auth_header(web_client):
    headers = {"X-Hub-Signature": "abcdef"}
    rsp = web_client.post("/github/", data=PAYLOAD_PR_CLOSED, headers=headers)
    assert rsp.status_code == 403


def test_invalid_auth_header(web_client):
    headers = {"X-Hub-Signature": "sha1=abcdef"}
    rsp = web_client.post("/github/", data=PAYLOAD_PR_CLOSED, headers=headers)
    assert rsp.status_code == 403


def test_valid_auth_header(web_client):
    headers = {"X-Hub-Signature": "sha1=adac1db7f924b4572c8379dc44caa415d44b2b1d"}
    rsp = web_client.post("/github/", data=PAYLOAD_PR_CLOSED, headers=headers)
    assert rsp.status_code == 200


def test_on_closed_merged_pr(web_client):
    headers = {"X-Hub-Signature": "sha1=adac1db7f924b4572c8379dc44caa415d44b2b1d"}
    rsp = web_client.post("/github/", data=PAYLOAD_PR_CLOSED, headers=headers)
    assert rsp.status_code == 200
    jj = scheduler.get_jobs_of_type("op_deploy")
    assert len(jj) == 1


def test_on_closed_unmerged_pr(web_client):
    headers = {"X-Hub-Signature": "sha1=7216f76b9a0d1b78b6ff77197f99fcab43f745d3"}
    rsp = web_client.post("/github/", data=PAYLOAD_PR_CLOSED_UNMERGED, headers=headers)
    assert rsp.status_code == 200
    assert not scheduler.get_jobs_of_type("op_deploy")


def test_on_opened_pr(web_client):
    headers = {"X-Hub-Signature": "sha1=e5d9fcbaa6acbc5031228155470fb82cbe12e018"}
    rsp = web_client.post("/github/", data=PAYLOAD_PR_OPENED, headers=headers)
    assert rsp.status_code == 200
    assert not scheduler.get_jobs_of_type("op_deploy")


def test_on_opened_issue(web_client):
    headers = {"X-Hub-Signature": "sha1=0022fa92c53686109b918c709518899662fe246f"}
    rsp = web_client.post("/github/", data=PAYLOAD_ISSUE_OPENED, headers=headers)
    assert rsp.status_code == 200
    assert not scheduler.get_jobs_of_type("op_deploy")

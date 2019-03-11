from unittest.mock import patch
import ebmbot_runner


GITHUB_VALID_DATA = {
    'action': 'closed',
    'pull_request': {'merged': 'true'}}
GITHUB_VALID_DATA_SIG = {
    "X-Hub-Signature": "sha1=cc26ba0d85cda109adedfb424ef7d65627c813aa"}


@patch('ebmbot_runner.deploy_live_delayed')
@patch('ebmbot_runner.SlackClient')
def test_github_webhook_works(mock_slack, mock_deploy):
    client = ebmbot_runner.app.test_client()
    client.post(
        '/github/',
        json=GITHUB_VALID_DATA,
        headers=GITHUB_VALID_DATA_SIG)
    mock_slack.assert_called()
    mock_deploy.assert_called()


@patch('ebmbot_runner.deploy_live_delayed')
@patch('ebmbot_runner.SlackClient')
def test_github_webhook_auth_no_header(mock_slack, mock_deploy):
    client = ebmbot_runner.app.test_client()
    result = client.post(
        '/github/',
        json=GITHUB_VALID_DATA)
    assert result.status_code == 403

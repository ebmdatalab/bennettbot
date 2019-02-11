import time

from datetime import datetime
from unittest.mock import patch
from unittest.mock import MagicMock
from ebmbot.openprescribing import deploy_live_delayed
from ebmbot.openprescribing import deploy_live_now
from ebmbot.openprescribing import reset_or_deploy_timer
from ebmbot.openprescribing import suppress_deploy
from ebmbot.openprescribing import cancel_suppression
from ebmbot.openprescribing import cancel_deploy_live
from ebmbot.openprescribing import show_status
import ebmbot_runner


@patch('ebmbot.openprescribing.reset_or_deploy_timer')
@patch('ebmbot.openprescribing.datetime')
def test_deploy_live_delayed_with_suppression(mock_datetime, mock_timer):
    now = datetime.now()
    # Set time to 1pm
    mock_datetime.now.return_value = datetime(
        *now.timetuple()[:3], 13, 00)
    mock_message = MagicMock()

    # Try do deploy during suppression period
    suppress_deploy(mock_message, "12:30", "14:30")
    assert 'Deployment suppressed' in str(mock_message.method_calls[-1])
    deploy_live_delayed(mock_message)
    assert 'Not deploying' in str(mock_message.method_calls[-1])
    mock_timer.assert_not_called()
    mock_message.reply.assert_called()

    # Check status
    show_status(mock_message)
    assert 'Deploys suppressed' in str(mock_message.method_calls[-1])

    # Cancel and try again
    cancel_suppression(mock_message)
    assert 'Cancelled' in str(mock_message.method_calls[-1])
    deploy_live_delayed(mock_message)
    assert 'Deploying in' in str(mock_message.method_calls[-1])

    # Set suppression to before now
    suppress_deploy(mock_message, "12:30", "12:59")
    deploy_live_delayed(mock_message)
    mock_timer.assert_called()
    assert 'Deploying in' in str(mock_message.method_calls[-1])


@patch('ebmbot.openprescribing.execute')
@patch('ebmbot.openprescribing.DEPLOY_DELAY', 0.7)
def test_delayed_deploy(mock_execute):
    mock_message = MagicMock()
    deploy_live_delayed(mock_message)
    time.sleep(0.4)
    assert 'Deploying in' in str(mock_message.method_calls[-1])

    # Check status
    show_status(mock_message)
    assert 'Deploy due in' in str(mock_message.method_calls[-1])

    # Make sure we've not deployed yet
    mock_execute.assert_not_called()

    # And now we should be
    time.sleep(1)
    mock_execute.assert_called()
    assert 'done' in str(mock_message.method_calls[-1])


@patch('ebmbot.openprescribing.execute')
def test_deploy_cancellation(mock_execute):
    mock_message = MagicMock()
    deploy_live_delayed(mock_message)
    cancel_deploy_live(mock_message)
    show_status(mock_message)
    assert 'No deploys in progress' in str(mock_message.method_calls[-1])


@patch('ebmbot.openprescribing.execute')
def test_immediate_deploy(mock_execute):
    mock_message = MagicMock()
    deploy_live_now(mock_message)
    time.sleep(0.01)
    mock_execute.assert_called()
    mock_message.reply.assert_called()


@patch('ebmbot_runner.deploy_live_delayed')
def test_github_webhook(mock_deploy):
    client = ebmbot_runner.app.test_client()
    client.post('/', json=dict(
        action='closed',
        merged='true'))
    mock_deploy.assert_called()

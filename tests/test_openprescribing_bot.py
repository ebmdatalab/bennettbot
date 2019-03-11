import time
from datetime import datetime
from unittest.mock import call
from unittest.mock import patch
from unittest.mock import MagicMock

import pytest

from bots.openprescribing.openprescribing import deploy_live_delayed
from bots.openprescribing.openprescribing import deploy_live_now
from bots.openprescribing.openprescribing import suppress_deploy
from bots.openprescribing.openprescribing import cancel_suppression
from bots.openprescribing.openprescribing import cancel_deploy_live
from bots.openprescribing.openprescribing import show_status
from bots.openprescribing import flags


@pytest.fixture(autouse=True)
def reset_flags():
    """Reset `global` flags between tests
    """
    old_flags = {}
    for possible_variable in dir(flags):
        if not possible_variable.startswith('__'):
            old_flags[possible_variable] = getattr(flags, possible_variable)

    yield
    for k, v in old_flags.items():
        setattr(flags, k, v)


@patch('bots.openprescribing.openprescribing.reset_or_deploy_timer')
@patch('bots.openprescribing.openprescribing.datetime')
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


@patch('bots.openprescribing.openprescribing.safe_execute')
@patch('bots.openprescribing.openprescribing.DEPLOY_DELAY', 1.0)
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


@patch('bots.openprescribing.openprescribing.safe_execute')
@patch('bots.openprescribing.openprescribing.DEPLOY_DELAY', 0.1)
def test_deploy_queued(mock_execute):
    """Two consecutive deployment calls should cause the second deployment
    to wait until the first is finished.

    """
    mock_message = MagicMock()
    mock_message.body = {'ts': 1234}   # Mock this being a threaded message
    deploy_live_delayed(mock_message)  # Deploying in N seconds
    flags.deploy_countdown = -1        # Simulate a long-running deployment
    deploy_live_delayed(mock_message)  # Deploy underway enqueues instead
    time.sleep(3)                      # Allow time for threads to start

    mock_message.assert_has_calls([
        call.reply(
            'Deploying in 0.1 seconds', in_thread=True),
        call.reply(
            "Deploy underway. Will start another when it's finished",
            in_thread=True),
        call.reply(
            'Deploy done', in_thread=True),
        call.reply(
            'Deploying in 0.1 seconds', in_thread=True),
        call.reply(
            'Deploy done', in_thread=True)])


@patch('bots.openprescribing.openprescribing.safe_execute')
def test_deploy_cancellation(mock_execute):
    mock_message = MagicMock()
    deploy_live_delayed(mock_message)
    cancel_deploy_live(mock_message)
    show_status(mock_message)
    assert 'No deploys in progress' in str(mock_message.method_calls[-1])


@patch('bots.openprescribing.openprescribing.safe_execute')
def test_immediate_deploy(mock_execute):
    mock_message = MagicMock()
    deploy_live_now(mock_message)
    time.sleep(0.01)
    mock_execute.assert_called()
    mock_message.reply.assert_called()


@patch('bots.openprescribing.openprescribing.safe_execute')
def test_immediate_deploy_fabric_env(mock_execute):
    mock_message = MagicMock()
    deploy_live_now(mock_message)
    time.sleep(0.01)
    mock_execute.assert_called()
    mock_message.reply.assert_called()

import time

from datetime import datetime
from unittest.mock import patch
from unittest.mock import MagicMock
from ebmbot.fdaaa_deploy import deploy_fdaaa
from ebmbot.fdaaa_deploy import update_fdaaa_staging
from fabfiles.clinicaltrials_act_tracker.fabfile import update

@patch('ebmbot.fdaaa_deploy.execute')
def test_deploy(mock_execute):
    mock_message = MagicMock()
    deploy_fdaaa(mock_message)
    assert 'Done' in str(mock_message.method_calls[-1])
    mock_execute.assert_called_with(update, environment='live')


@patch('ebmbot.fdaaa_deploy.execute')
def test_update(mock_execute):
    mock_message = MagicMock()
    update_fdaaa_staging(mock_message)
    assert 'Updating' in str(mock_message.method_calls[-1])
    mock_execute.assert_called_with(update, environment='staging')

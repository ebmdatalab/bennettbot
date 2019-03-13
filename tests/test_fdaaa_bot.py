from unittest.mock import patch
from unittest.mock import MagicMock
from bots.fdaaa.fdaaa_deploy import deploy_fdaaa
from bots.fdaaa.fdaaa_deploy import fdaaa_help
from bots.fdaaa.fdaaa_deploy import update_fdaaa_staging
from fabfiles.clinicaltrials_act_tracker.fabfile import update


def test_help():
    mock_message = MagicMock()
    fdaaa_help(mock_message)
    assert 'fdaaa deploy' in str(mock_message.method_calls[-1])


@patch('bots.fdaaa.fdaaa_deploy.safe_execute')
def test_deploy(mock_execute):
    mock_message = MagicMock()
    deploy_fdaaa(mock_message)
    assert 'Done' in str(mock_message.method_calls[-1])
    mock_execute.assert_called_with(
        update, hosts=['smallweb1.openprescribing.net'], environment='live')


@patch('bots.fdaaa.fdaaa_deploy.safe_execute')
def test_update(mock_execute):
    mock_message = MagicMock()
    update_fdaaa_staging(mock_message)
    assert 'Updating' in str(mock_message.method_calls[-1])
    mock_execute.assert_called_with(
        update, hosts=['smallweb1.openprescribing.net'], environment='staging')

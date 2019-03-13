from unittest.mock import MagicMock

from bots.core.core import core_help


def test_help():
    mock_message = MagicMock()
    core_help(mock_message)
    assert 'op help' in str(mock_message.method_calls[-1])

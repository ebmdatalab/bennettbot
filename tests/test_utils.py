import pytest
from unittest.mock import patch

from tests import fabfile_example
from bots.utils import safe_execute
from bots.utils import NonExitingError


# Because py.test replaces stdin with a StringIO, but fabric wants to
# do a low-level `select` on a stdin which is a file, we have to patch
# fabric's input loop to work around errors (there appears to be no
# programmatic way of doing this, or at least not one I could get to
# work)
def test_run():
    with patch('fabric.operations.input_loop'):
        result = safe_execute(fabfile_example.do_run)
        assert result['localhost'] == "hello world"


def test_disallowed():
    with patch('fabric.operations.input_loop'):
        with pytest.raises(NonExitingError) as excinfo:
            safe_execute(fabfile_example.do_disallowed_thing)
        assert "Fatal error" in excinfo.value.stderr


def test_abort():
    with pytest.raises(NonExitingError) as excinfo:
        safe_execute(fabfile_example.do_abort)
    assert "Fatal error: some error" in excinfo.value.stderr

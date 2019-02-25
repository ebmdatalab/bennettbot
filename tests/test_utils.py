import getpass
import pytest
from unittest.mock import patch

from tests import fabfile_example
from bots.utils import safe_execute
from bots.utils import NonExitingError


# These tests assume the user running the tests has passwordless SSH
# access to localhost. If the tests are hanging, it's probably waiting
# on password input.
#
# See `.travis.yml` for how we set this up before running the tests
# there.
HOSTS = ["{}@localhost".format(getpass.getuser())]


# Because py.test replaces stdin with a StringIO, but fabric wants to
# do a low-level `select` on a stdin which is a file, we have to patch
# fabric's input loop to work around errors (there appears to be no
# programmatic way of doing this, or at least not one I could get to
# work)
def test_run():
    with patch('fabric.operations.input_loop'):
        result = safe_execute(fabfile_example.do_run, hosts=HOSTS)
        assert result[HOSTS[0]] == "hello world"


def test_disallowed():
    with patch('fabric.operations.input_loop'):
        with pytest.raises(NonExitingError) as excinfo:
            safe_execute(fabfile_example.do_disallowed_thing, hosts=HOSTS)
        assert "Fatal error" in excinfo.value.stderr


def test_abort():
    with pytest.raises(NonExitingError) as excinfo:
        safe_execute(fabfile_example.do_abort, hosts=HOSTS)
    assert "Fatal error: some error" in excinfo.value.stderr

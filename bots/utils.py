import contextlib
import io
import logging
import traceback

from fabric.api import settings
from fabric.tasks import execute
from slackbot_settings import FABRIC_ENV


class NonExitingError(Exception):
    def __init__(self, original, stderr):
        self.original = original
        self.stderr = stderr

    def __str__(self):
        return "NonExitingError wrapping {}\n\n{}".format(
            self.original,
            self.stderr)


def safe_execute(cmd, *args, **kwargs):
    """Execute fabric command, catching and logging SystemExit along with
    stderr, so we have a chance to close threads cleaning with an exit
    message.

    Requires explicit `hosts` value. This is because by convention
    fabfiles set this in a global-and-non-threadsafe module; in turn,
    this means that running more than one fabric operation at a time
    may lead to the commands running on the wrong hosts.

    """

    captured_stderr = io.StringIO()
    assert 'hosts' in kwargs, "You must supply a `hosts` keyword argument"
    try:
        with contextlib.redirect_stderr(captured_stderr):
            with settings(**FABRIC_ENV):
                result = execute(cmd, *args, **kwargs)
    except BaseException as e:
        # BaseException includes SystemExit, whereas Exception doesn't.
        captured_stderr.seek(0)
        stderr = captured_stderr.read()
        if isinstance(e, SystemExit):
            msg = "Fabric aborted with exiting exception %s, %s, %s\n\n%s"
        else:
            msg = "Fabric aborted with exception %s, %s, %s\n\n%s"
        stack = traceback.format_tb(e.__traceback__)
        logging.info(msg, type(e), e, stderr, stack)
        raise NonExitingError(e, stderr)
    return result

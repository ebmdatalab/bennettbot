import contextlib
import io
import logging
from fabric.tasks import execute


class NonExitingError(Exception):
    def __init__(self, original, stderr):
        self.original = original
        self.stderr = stderr

    def __str__(self):
        return "NonExitingError wrapping {}\n\n".format(
            self.original,
            self.stderr)


def safe_execute(cmd, *args, **kwargs):
    """Execute fabric command, catching and logging SystemExit along with
    stderr.

    This is because Fabric `abort` operations raise SystemExit, which
    (uncaught) leads to our calling thread dying before a response can
    be sent to Slack.

    """
    captured_stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(captured_stderr):
            result = execute(cmd, *args, **kwargs)
    except SystemExit as e:
        captured_stderr.seek(0)
        stderr = captured_stderr.read()
        logging.info("Fabric aborted with exiting exception %s, %s, %s",
                     type(e), e, stderr)
        raise NonExitingError(e, stderr)
    return result

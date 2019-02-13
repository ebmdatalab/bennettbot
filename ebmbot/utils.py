import logging
from fabric.tasks import execute


class NonExitingError(Exception):
    def __init__(self, original):
        self.original = original

    def __str__(self):
        return "NonExitingError wrapping {}".format(self.original)


def safe_execute(cmd, *args, **kwargs):
    """Execute fabric command, catching and logging SystemExit

    Fabric `abort` operations raise SystemExit, which leads to our
    calling thread dying before a response can be returned.
    """
    try:
        result = execute(cmd, *args, **kwargs)
    except BaseException as e:
        # System-exiting exceptions don't inherit from Exception, and
        # we want to catch them too
        logging.info("Fabric aborted with exiting exception %s, %s", type(e), e)
        raise NonExitingError(e)
    return result

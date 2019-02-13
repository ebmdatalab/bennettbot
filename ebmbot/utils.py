import logging
from fabric.tasks import execute


def safe_execute(cmd, *args, **kwargs):
    """Execute fabric command, catching and logging SystemExit

    Fabric `abort` operations raise SystemExit, which leads to our
    calling thread dying before a response can be returned.
    """
    try:
        result = execute(cmd, *args, **kwargs)
    except SystemExit as e:
        logging.info("Fabric aborted with %s", e)
        result = "Error: {}".format(e)
    return result

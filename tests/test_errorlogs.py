import subprocess
from os import environ
from pathlib import Path

import pytest

from ebmbot import settings

from .test_dispatcher import build_log_dir


def setup_failed_logs():
    log_dir = Path(build_log_dir("err_bad_job"))
    log_dir.mkdir(exist_ok=True, parents=True)
    with open(Path(log_dir) / "stderr", "w") as f:
        f.write("foo")
    return log_dir


@pytest.mark.parametrize(
    "option,expected_output",
    [
        ("-h", b"Reading head of error log"),
        ("-t", b"Reading tail of error log"),
        ("-g", b"Invalid option"),
    ],
)
def test_errorlogs(option, expected_output):
    log_dir = setup_failed_logs()
    errorlogs_workspace = Path(__file__).parent.parent / "workspace" / "errorlogs"

    rv = subprocess.run(
        f"/bin/bash show.sh {option} {log_dir.resolve()}",
        cwd=errorlogs_workspace,
        env={**environ, "PYTHONPATH": errorlogs_workspace.parent},
        shell=True,
        capture_output=True,
    )
    assert expected_output in rv.stdout


def test_errorlogs_with_different_host_logs_dir():
    log_dir = setup_failed_logs()
    errorlogs_workspace = Path(__file__).parent.parent / "workspace" / "errorlogs"

    # Log files are located at LOGS_DIR (in prod, a path to the logs folder in the
    # mounted volume). This is aliased to HOST_LOGS_DIR in slack messages, so that
    # failed commands tell users where to find logs on the host filesystem
    # So if a user calls the command with the host location, it needs to
    # look for the file in the real LOGS_DIR location
    dummy_host_logs = "/hosts/dummy_logs"
    host_log_dir = str(log_dir).replace(str(settings.LOGS_DIR), dummy_host_logs)

    rv = subprocess.run(
        f"/bin/bash show.sh -h {host_log_dir}",
        cwd=errorlogs_workspace,
        env={
            **environ,
            "PYTHONPATH": errorlogs_workspace.parent,
            "LOGS_DIR": settings.LOGS_DIR.resolve(),
            "HOST_LOGS_DIR": dummy_host_logs,
        },
        shell=True,
        capture_output=True,
    )
    assert b"Reading head of error log" in rv.stdout


def test_errorlogs_file_not_found():
    log_dir = setup_failed_logs()
    errorlogs_workspace = Path(__file__).parent.parent / "workspace" / "errorlogs"

    rv = subprocess.run(
        f"/bin/bash show.sh -h {log_dir / 'unk'}",
        cwd=errorlogs_workspace,
        env={**environ, "PYTHONPATH": errorlogs_workspace.parent},
        shell=True,
        capture_output=True,
    )
    assert b"not found" in rv.stdout

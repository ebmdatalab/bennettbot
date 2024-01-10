import re

import pytest

from ebmbot import settings
from ebmbot.job_configs import build_config


def test_build_config():
    raw_config = {
        "ns1": {
            "jobs": {
                "good_job": {"run_args_template": "cat [poem]"},
                "bad_job": {"run_args_template": "dog [poem]"},
            },
            "slack": [
                {
                    "command": "read poem [poem]",
                    "help": "read a poem",
                    "action": "schedule_job",
                    "job_type": "good_job",
                }
            ],
        },
        "ns2": {
            "jobs": {
                "good_job": {"run_args_template": "cat [poem]", "report_stdout": True},
                "bad_job": {"run_args_template": "dog [poem]", "report_success": False},
            },
            "slack": [
                {
                    "command": "read poem [poem]",
                    "help": "read a poem",
                    "action": "schedule_job",
                    "job_type": "good_job",
                }
            ],
        },
        "ns3": {
            "jobs": {
                "good_python_job": {
                    "run_args_template": "python jobs.py",
                    "report_stdout": True,
                },
                "bad_python_job": {
                    "run_args_template": "python jobs.py",
                    "report_stdout": True,
                },
            },
            "slack": [
                {
                    "command": "hello world",
                    "help": "say hello world",
                    "action": "schedule_job",
                    "job_type": "good_python_job",
                }
            ],
        },
        # Minimal config for a job with an existing workspace dir
        "test": {
            "jobs": {
                "good_job": {"run_args_template": "echo Hello"},
            },
            "slack": [],
        },
    }

    config = build_config(raw_config)
    # Assert that in tests, settings.WORKSPACE_DIR and
    # settings.WRITEABLE_WORKSPACE_DIR are different. Jobs that don't already have
    # a namespace dir will useWRITEABLE_WORKSPACE_DIR
    assert settings.WORKSPACE_DIR != settings.WRITEABLE_WORKSPACE_DIR
    assert config == {
        "jobs": {
            "ns1_good_job": {
                "run_args_template": "cat [poem]",
                "report_stdout": False,
                "report_format": "text",
                "report_success": True,
            },
            "ns1_bad_job": {
                "run_args_template": "dog [poem]",
                "report_stdout": False,
                "report_format": "text",
                "report_success": True,
            },
            "ns2_good_job": {
                "run_args_template": "cat [poem]",
                "report_stdout": True,
                "report_format": "text",
                "report_success": True,
            },
            "ns2_bad_job": {
                "run_args_template": "dog [poem]",
                "report_stdout": False,
                "report_format": "text",
                "report_success": False,
            },
            "ns3_good_python_job": {
                "run_args_template": "python jobs.py",
                "report_stdout": True,
                "report_format": "text",
                "report_success": True,
            },
            "ns3_bad_python_job": {
                "run_args_template": "python jobs.py",
                "report_stdout": True,
                "report_format": "text",
                "report_success": True,
            },
            "test_good_job": {
                "run_args_template": "echo Hello",
                "report_stdout": False,
                "report_format": "text",
                "report_success": True,
            },
        },
        "slack": [
            {
                "command": "ns1 read poem [poem]",
                "job_type": "ns1_good_job",
                "help": "read a poem",
                "action": "schedule_job",
                "regex": re.compile("^ns1 read poem (.+?)$"),
                "template_params": ["poem"],
                "delay_seconds": 0,
            },
            {
                "command": "ns2 read poem [poem]",
                "job_type": "ns2_good_job",
                "help": "read a poem",
                "action": "schedule_job",
                "regex": re.compile("^ns2 read poem (.+?)$"),
                "template_params": ["poem"],
                "delay_seconds": 0,
            },
            {
                "command": "ns3 hello world",
                "job_type": "ns3_good_python_job",
                "help": "say hello world",
                "action": "schedule_job",
                "regex": re.compile("^ns3 hello world$"),
                "template_params": [],
                "delay_seconds": 0,
            },
        ],
        "help": {
            "ns1": [["ns1 read poem [poem]", "read a poem"]],
            "ns2": [["ns2 read poem [poem]", "read a poem"]],
            "ns3": [["ns3 hello world", "say hello world"]],
            "test": [],
        },
        "fabfiles": {},
        "workspace_dir": {
            "ns1": settings.WRITEABLE_WORKSPACE_DIR,
            "ns2": settings.WRITEABLE_WORKSPACE_DIR,
            "ns3": settings.WRITEABLE_WORKSPACE_DIR,
            "test": settings.WORKSPACE_DIR,
        },
    }


def test_build_config_with_bad_job_config():
    # fmt: off
    raw_config = {
        "ns": {
            "jobs": {
                "good_job": {"run_args_templat": "cat [poem]"}
            },
            "slack": []
        }
    }
    # fmt: on

    with pytest.raises(RuntimeError) as e:
        build_config(raw_config)
    assert "missing keys" in str(e)

    # fmt: off
    raw_config = {
        "ns": {
            "jobs": {
                "good_job": {
                    "run_args_template": "cat [poem]",
                    "extra_param": 123
                }
            },
            "slack": []
        }
    }
    # fmt: on

    with pytest.raises(RuntimeError) as e:
        build_config(raw_config)
    assert "extra keys" in str(e)


def test_build_config_with_bad_slack_config():
    # fmt: off
    raw_config = {
        "ns": {
            "jobs": {},
            "slack": [
                {
                    "command": "do good job",
                    "action": "schedule_job",
                    "job_type": "good_job",
                }
            ]
        }
    }
    # fmt: on

    with pytest.raises(RuntimeError) as e:
        build_config(raw_config)
    assert "missing keys" in str(e)

    # fmt: off
    raw_config = {
        "ns": {
            "jobs": {
                "good_job": {
                    "run_args_template": "cat [poem]",
                }
            },
            "slack": [
                {
                    "command": "do good job",
                    "help": "do job well",
                    "action": "schedule_job",
                    "job_type": "good_job",
                    "extra_param": 123,
                }
            ]
        }
    }
    # fmt: on

    with pytest.raises(RuntimeError) as e:
        build_config(raw_config)
    assert "extra keys" in str(e)

    # fmt: off
    raw_config = {
        "ns": {
            "jobs": {
                "good_job": {
                    "run_args_template": "cat [poem]",
                }
            },
            "slack": [
                {
                    "command": "do good job",
                    "help": "do job well",
                    "action": "schedule_job",
                    "job_type": "odd_job",
                }
            ]
        }
    }
    # fmt: on

    with pytest.raises(RuntimeError) as e:
        build_config(raw_config)
    assert "unknown job type" in str(e)


def test_build_config_with_invalid_report_format():
    # fmt: off
    raw_config = {
        "ns": {
            "jobs": {
                "good_job": {
                    "run_args_template": "cat [poem]",
                    "report_format": "unknown"
                }
            },
            "slack": []
        }
    }

    with pytest.raises(RuntimeError) as e:
        build_config(raw_config)
    assert "invalid report_format" in str(e)

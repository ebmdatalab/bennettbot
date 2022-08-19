import re

import pytest

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
                    "type": "schedule_job",
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
                    "type": "schedule_job",
                    "job_type": "good_job",
                }
            ],
        },
        "ns3": {
            "python_file": "jobs.py",
            "jobs": {
                "good_python_job": {
                    "run_args_template": "",
                    "report_stdout": True,
                    "python_function": "hello_world",
                },
                "bad_python_job": {
                    "run_args_template": "",
                    "report_stdout": True,
                    "python_function": "unknown",
                },
            },
            "slack": [
                {
                    "command": "hello world",
                    "help": "say hello world",
                    "type": "schedule_job",
                    "job_type": "good_python_job",
                }
            ],
        },
    }

    config = build_config(raw_config)
    assert config == {
        "jobs": {
            "ns1_good_job": {
                "run_args_template": "cat [poem]",
                "report_stdout": False,
                "report_success": True,
                "python_function": None,
            },
            "ns1_bad_job": {
                "run_args_template": "dog [poem]",
                "report_stdout": False,
                "report_success": True,
                "python_function": None,
            },
            "ns2_good_job": {
                "run_args_template": "cat [poem]",
                "report_stdout": True,
                "report_success": True,
                "python_function": None,
            },
            "ns2_bad_job": {
                "run_args_template": "dog [poem]",
                "report_stdout": False,
                "report_success": False,
                "python_function": None,
            },
            "ns3_good_python_job": {
                "run_args_template": "",
                "report_stdout": True,
                "report_success": True,
                "python_function": "hello_world",
            },
            "ns3_bad_python_job": {
                "run_args_template": "",
                "report_stdout": True,
                "report_success": True,
                "python_function": "unknown",
            },
        },
        "slack": [
            {
                "command": "ns1 read poem [poem]",
                "job_type": "ns1_good_job",
                "help": "read a poem",
                "type": "schedule_job",
                "regex": re.compile("^ns1 read poem (.+?)$"),
                "template_params": ["poem"],
                "delay_seconds": 0,
            },
            {
                "command": "ns2 read poem [poem]",
                "job_type": "ns2_good_job",
                "help": "read a poem",
                "type": "schedule_job",
                "regex": re.compile("^ns2 read poem (.+?)$"),
                "template_params": ["poem"],
                "delay_seconds": 0,
            },
            {
                "command": "ns3 hello world",
                "job_type": "ns3_good_python_job",
                "help": "say hello world",
                "type": "schedule_job",
                "regex": re.compile("^ns3 hello world$"),
                "template_params": [],
                "delay_seconds": 0,
            },
        ],
        "help": {
            "ns1": [["ns1 read poem [poem]", "read a poem"]],
            "ns2": [["ns2 read poem [poem]", "read a poem"]],
            "ns3": [["ns3 hello world", "say hello world"]],
        },
        "fabfiles": {},
        "python_files": {"ns3": "jobs.py"},
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
                    "type": "schedule_job",
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
                    "type": "schedule_job",
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
                    "type": "schedule_job",
                    "job_type": "odd_job",
                }
            ]
        }
    }
    # fmt: on

    with pytest.raises(RuntimeError) as e:
        build_config(raw_config)
    assert "unknown job type" in str(e)

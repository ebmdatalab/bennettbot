from ebmbot.job_configs import build_config


# fmt: off
raw_config = {
    "test": {
        "python_file": "jobs.py",
        "jobs": {
            "good_job": {
                "run_args_template": "cat poem",
            },
            "paramaterised_job": {
                "run_args_template": "cat {path}",
            },
            "paramaterised_job_2": {
                "run_args_template": "echo {thing_to_echo}",
            },
            "reported_job": {
                "run_args_template": "cat poem",
                "report_stdout": True,
            },
            "unreported_job": {
                "run_args_template": "cat poem",
                "report_success": False,
            },
            "job_to_test_callback": {
                "run_args_template": "echo $EBMBOT_CALLBACK_URL",
            },
            "bad_job": {
                "run_args_template": "cat no-poem",
            },
            "really_bad_job": {
                "run_args_template": "dog poem",
            },
            "job_with_url": {
                "run_args_template": "curl {url}",
            },
            "good_python_job": {
                "run_args_template": "",
                "python_function": "hello_world",
                "report_stdout": True
            },
            "bad_python_job": {
                "run_args_template": "",
                "python_function": "unknown",
                "report_stdout": True
            },
            "parameterised_python_job": {
                "run_args_template": "",
                "python_function": "hello_world",
                "report_stdout": True
            },
            "good_python_job_with_blocks": {
                "run_args_template": "",
                "python_function": "hello_world_blocks",
                "report_stdout": True,
                "report_format": "blocks"
            },
            "bad_python_job_with_blocks": {
                "run_args_template": "",
                "python_function": "hello_world_blocks_error",
                "report_stdout": True,
                "report_format": "blocks"
            },
        },
        "slack": [
            {
                "command": "do job [n]",
                "help": "do the job",
                "type": "schedule_job",
                "job_type": "good_job",
                "delay_seconds": 60,
            },
            {
                "command": "cancel job",
                "help": "cancel the job",
                "type": "cancel_job",
                "job_type": "good_job",
            },
            {
                "command": "suppress job from [start_at] to [end_at]",
                "help": "suppress the job",
                "type": "schedule_suppression",
                "job_type": "good_job",
            },
            {
                "command": "cancel suppression",
                "help": "don't suppress the job",
                "type": "cancel_suppression",
                "job_type": "good_job",
            },
            {
                "command": "do url [url]",
                "help": "do a job with a url",
                "type": "schedule_job",
                "job_type": "job_with_url",
                "delay_seconds": 0,
            },
            {
                "command": "do python job",
                "help": "run a python function",
                "type": "schedule_job",
                "job_type": "good_python_job",
                "delay_seconds": 0,
            },
            {
                "command": "do python blocks job",
                "help": "run a python function",
                "type": "schedule_job",
                "job_type": "good_python_job_with_blocks",
                "delay_seconds": 0,
            },
        ],
    },
    "test1": {
        "jobs": {
            "good_job": {
                "run_args_template": "cat poem",
            },
        },
        "slack": [],
    }
}
# fmt: on


config = build_config(raw_config)

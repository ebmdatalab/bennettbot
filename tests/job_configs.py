from ebmbot.job_configs import build_config

# fmt: off
raw_config = {
    "test": {
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
        ],
    }
}
# fmt: on


config = build_config(raw_config)

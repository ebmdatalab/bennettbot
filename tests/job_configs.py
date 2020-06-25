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
            "reported_job": {
                "run_args_template": "cat poem",
                "report_stdout": True,
            },
            "job_with_callback": {
                "run_args_template": "cat poem",
                "add_callback_args": True,
            },
            "bad_job": {
                "run_args_template": "cat no-poem",
            },
            "really_bad_job": {
                "run_args_template": "dog poem",
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
        ],
    }
}
# fmt: on


config = build_config(raw_config)

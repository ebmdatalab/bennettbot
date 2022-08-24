# ebmbot

ebmbot is a service for running jobs in reponse to Slack commands and GitHub webhooks.

A job runs a bash command in a given directory.
Jobs are organised by namespace, and are defined in `job_configs.py`.

There are three moving parts:

* `bot.py` -- a [slack bolt app](https://github.com/slackapi/bolt-python) that listens for jobs via Slack commands (see also [Slack docs](https://api.slack.com/bolt))
* `webserver/` -- a Flask app that listens for jobs via webhooks from GitHub
* `dispatcher.py` -- a Python script that sits in a loop and runs the jobs

They communicate via a table in a SQLite database that acts as a simple job queue.
The database schema is in `connection.py`, and functions for putting jobs onto the queue (and taking them off again) are in `scheduler.py`.


## Deployment docs

Please see the [additional information](DEPLOY.md).


## Developer docs

Please see the [additional information](DEVELOPERS.md).

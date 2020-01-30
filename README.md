# ebmbot

ebmbot is a service for running jobs in reponse to Slack commands and GitHub webhooks.

A job runs a bash command in a given directory.
Jobs are organised by namespace, and are defined in `job_configs.py`.

There are three moving parts:

* `bot.py` -- a [slackbot](https://github.com/lins05/slackbot) that listens for jobs via Slack commands
* `server.py` -- a Flask app that listens for jobs via webhooks from GitHub
* `dispatcher.py` -- a Python script that sits in a loop and runs the jobs

They communicate via a table in a SQLite database that acts as a simple job queue.
The database schema is in `connection.py`, and functions for putting jobs onto the queue (and taking them off again) are in `scheduler.py`.


### deployment

ebmbot is deployed on smallweb1 and is managed by systemd.

* To deploy: `fab deploy`
* To view logs: `sudo journalctl -u app.ebmbot.* -b -f`


### development

* Set up a virtual environment
* Install dependencies: `pip install -r requirements.txt`
* Copy environment: `cp environment-sample environment`
* Run individual services: `. environment && python -m ebmbot.[service]`
* Run tests: `pytest`
* Run tests under coverage: `pytest --cov=.`
* Fix formatting: `./fix_formatting.sh`

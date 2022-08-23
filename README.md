# ebmbot

ebmbot is a service for running jobs in reponse to Slack commands and GitHub webhooks.

A job runs a bash command in a given directory.
Jobs are organised by namespace, and are defined in `job_configs.py`.

There are three moving parts:

* `bot.py` -- a [slack bolt app](https://github.com/slackapi/bolt-python) that listens for jobs via Slack commands (see also [Slack docs](https://api.slack.com/bolt))
* `server.py` -- a Flask app that listens for jobs via webhooks from GitHub
* `dispatcher.py` -- a Python script that sits in a loop and runs the jobs

They communicate via a table in a SQLite database that acts as a simple job queue.
The database schema is in `connection.py`, and functions for putting jobs onto the queue (and taking them off again) are in `scheduler.py`.

## Creating the Slack app
(This should only need to be done once).

ebmbot needs a new-stye Slack app and uses 
[socket mode](https://slack.dev/bolt-python/concepts#socket-mode) to listen for messages.
To create one:

### Create the app
1. visit <https://api.slack.com/apps>
2. Click the "Create new app" button and choose the "From scratch" option
3. Name the app and select the Bennett Institute workspace to develop it in.  
   After creating the app, you'll be dropped into the app's page.

### Enable socket mode and create app token
1. Settings > Socket Mode
2. Enable Socket Mode; this will create the app token.  Give the token a name and accept 
   the default scope assigned (`connections:write`).
3. Go to Settings > Basic information, and under App Level Tokens you'll now see the token
   you just created.  This token starts `xapp-` and should be the value set for the
   `SLACK_APP_TOKEN` environment variable

### Add event subscriptions
Add event subscriptions to allow the app to be notified of events in Slack/
1. Features > Event subscriptions; toggle on
2. In Subscribe to bot events, add the following events:
   - message.channels
   - message.groups
   - message.im
   - message.mpim
   - channel_created
   - app_mention
3. Save changes

### Add Bot scopes
Adding the event subscriptions above automatically adds the required oauth scopes for the
events.  We need to add some more:
1. Features > OAuth & Permissions: scroll down to Scopes
   You should see the following Bot Token Scopes already assigned:
   - `channels:history`
   - `groups:history`
   - `im:history`
   - `mpim:history`
   - `channels:read`
   - `app_mentions:read`
2. Add the following additional scopes:
   - `channels:join`
   - `users:read`
   - `groups:read`
   - `mpim:read`
   - `im:read`
   - `reactions:write`
   - `chat:write`

### Allow users to DM the app
1. Features > App Home
2. Under Messages Tabs, ensure the "Allow users to send Slash commands and messages from
  the messages tab" is ticked.

### Install the app
1. Features > OAuth & Permissions
2. Under "OAuth Tokens for Your Workspace", click "Install to Workspace"
3. This will generate the bot token (starts `xoxb-`)

If you update any scopes after installing the app, you'll need to reinstall it (slack will
usually prompt for this).

### Set environment variables
The following slack environment variables need to be set:
- `SLACK_LOGS_CHANNEL`: channel where scheduled job notifications will be posted
- `SLACK_TECH_SUPPORT_CHANNEL`: channel where tech-support requests will be reposted
- `SLACK_APP_TOKEN`: app-level token generated above (starts `xapp-`); found on the app's Basic Information page
- `SLACK_BOT_TOKEN`: bot token generated above (starts `xoxb-`); found on the app's Oauth and Permissions page 
- `SLACK_SIGNING_SECRET`: Found on the app's Basic Information page, under App Credentials
- `SLACK_APP_USERNAME`: The app's default name (and the name users will refer to the Bot as in Slack); found under Features > App Home

## deployment

ebmbot is deployed on smallweb1 and is managed by systemd.

* To deploy: `fab deploy`
* To view logs: `sudo journalctl -u app.ebmbot.* -b -f`


## development

### Set up a test slack workspace and app

Create a [new slack workspace](https://slack.com/intl/en-gb/get-started#/createnew) to use for testing.

Follow the steps above to create a slack app with the required scopes and install it into
you test workspace.

### Set up development environment
* Set up a virtual environment
* Install dependencies: `pip install -r requirements.txt`
* Copy environment: `cp environment-sample environment`

Edit `environment` with the slack app tokens etc for the test slack app. 

### Run individual services: 
`. environment && python -m ebmbot.[service]`

To run the slack bot and test jobs, run both the bot and dispatcher:
```
. environment && python -m ebmbot.bot
. environment && python -m ebmbot.dispatcher
```

### Run tests and checks: 
* All tests: pytest`
* Run tests under coverage: `pytest --cov=.`
* Check formatting: `./check_formatting.sh`
* Fix formatting: `./fix_formatting.sh`

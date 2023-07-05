# Deployment

ebmbot is deployed on smallweb1 and is managed by systemd.

* To deploy: `fab deploy`
* To view logs: `sudo journalctl -u app.ebmbot.* -b -f`

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

Copy `dotenv-sample` to `.env` and update with relevant environment variables. See also
comments in `ebmbot/settings.py`.

The following slack environment variables need to be set:
- `SLACK_LOGS_CHANNEL`: channel where scheduled job notifications will be posted
- `SLACK_TECH_SUPPORT_CHANNEL`: channel where tech-support requests will be reposted
- `SLACK_APP_TOKEN`: app-level token generated above (starts `xapp-`); found on the app's Basic Information page
- `SLACK_BOT_TOKEN`: bot token generated above (starts `xoxb-`); found on the app's Oauth and Permissions page
- `SLACK_SIGNING_SECRET`: Found on the app's Basic Information page, under App Credentials
- `SLACK_APP_USERNAME`: The app's default name (and the name users will refer to the Bot as in Slack); found under Features > App Home

The following webhook environment variables need to be set. These relate to callbacks from
OpenPrescribing, and are configured at https://github.com/ebmdatalab/openprescribing/settings/hooks/85994427.
- `GITHUB_WEBHOOK_SECRET`
- `WEBHOOK_ORIGIN`
- `EBMBOT_WEBHOOK_SECRET`

The following environment variable allows the bot to authenticate with Github to retrieve
project information.
- `DATA_TEAM_GITHUB_API_TOKEN`: Note that this must be a classic PAT (not fine-grained) and
  needs the `repo` and `read:project` scope

GCP service account credentials:
- `GCP_CREDENTIALS_PATH`

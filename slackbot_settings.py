import logging
import os

# "Bot User OAuth Access Token" from https://api.slack.com/apps/A6B85C8KC/oauth
API_TOKEN = os.environ['SLACK_BOT_ACCESS_TOKEN']
DEFAULT_REPLY = "I'm sorry, but I didn't understand you"
ERRORS_TO = 'tech'

PLUGINS = [
    'ebmbot.openprescribing',
    'ebmbot.hal'
]

GITHUB_WEBHOOK_PORT = 9999

logging.basicConfig(
    filename='/var/log/ebmbot/runner.log',
    level=logging.DEBUG)

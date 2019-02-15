import logging
import os

from fabric.api import env

# "Bot User OAuth Access Token" from https://api.slack.com/apps/A6B85C8KC/oauth
API_TOKEN = os.environ['SLACK_BOT_ACCESS_TOKEN']
DEFAULT_REPLY = "I'm sorry, but I didn't understand you"
ERRORS_TO = 'tech'

PLUGINS = [
    'bots.openprescribing.openprescribing',
    'bots.fdaaa.fdaaa_deploy',
    'bots.hal.hal'
]

GITHUB_WEBHOOK_PORT = 9999

FABRIC_ENV = {
    'user': 'ebmbot',
    'disable_known_hosts': True,
    'colorize_errors': False
}

try:
    # Production location
    logging.basicConfig(
        filename='/var/log/ebmbot/runner.log',
        format="%(asctime)s %(message)s",
        level=logging.DEBUG)
except FileNotFoundError:
    logging.basicConfig(
        handlers=[logging.StreamHandler()],
        format="%(asctime)s %(message)s",
        level=logging.DEBUG)

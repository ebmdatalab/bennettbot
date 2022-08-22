import os
from os.path import abspath, dirname, join

APPLICATION_ROOT = dirname(dirname(abspath(__file__)))

DB_PATH = os.environ.get("DB_PATH", join(APPLICATION_ROOT, "ebmbot.db"))
WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", join(APPLICATION_ROOT, "workspace"))
LOGS_DIR = os.environ["LOGS_DIR"]
SLACK_LOGS_CHANNEL = os.environ["SLACK_LOGS_CHANNEL"]
SLACK_TECH_SUPPORT_CHANNEL = os.environ["SLACK_TECH_SUPPORT_CHANNEL"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
SLACK_APP_USERNAME = os.environ["SLACK_APP_USERNAME"]

# Should match "Payload URL" from
# https://github.com/ebmdatalab/openprescribing/settings/hooks/85994427
WEBHOOK_ORIGIN = os.environ["WEBHOOK_ORIGIN"]

# "Secret" from https://github.com/ebmdatalab/openprescribing/settings/hooks/85994427
GITHUB_WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"].encode("ascii")

# A secret that we generate ourselves
EBMBOT_WEBHOOK_SECRET = os.environ["EBMBOT_WEBHOOK_SECRET"].encode("ascii")

# TTL in seconds for webhook token
EBMBOT_WEBHOOK_TOKEN_TTL = 60 * 60

EBMBOT_PATH = os.environ["EBMBOT_PATH"]

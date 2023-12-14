from pathlib import Path

from environs import Env


env = Env()
env.read_env()

APPLICATION_ROOT = Path(__file__).resolve().parent.parent
# If running in docker, this is /app/
EBMBOT_PATH = env.str("EBMBOT_PATH", default=APPLICATION_ROOT)

DB_PATH = env.path("DB_PATH", default=APPLICATION_ROOT / "ebmbot.db")
WORKSPACE_DIR = env.path("WORKSPACE_DIR", default=APPLICATION_ROOT / "workspace")
LOGS_DIR = env.path("LOGS_DIR")
SLACK_LOGS_CHANNEL = env.str("SLACK_LOGS_CHANNEL")
SLACK_TECH_SUPPORT_CHANNEL = env.str("SLACK_TECH_SUPPORT_CHANNEL")
SLACK_BOT_TOKEN = env.str("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = env.str("SLACK_APP_TOKEN")
SLACK_SIGNING_SECRET = env.str("SLACK_SIGNING_SECRET")
SLACK_APP_USERNAME = env.str("SLACK_APP_USERNAME")

# Should match "Payload URL" from
# https://github.com/ebmdatalab/openprescribing/settings/hooks/85994427
WEBHOOK_ORIGIN = env.str("WEBHOOK_ORIGIN")

# "Secret" from https://github.com/ebmdatalab/openprescribing/settings/hooks/85994427
GITHUB_WEBHOOK_SECRET = env.str("GITHUB_WEBHOOK_SECRET").encode("ascii")

# Path to credentials of gdrive@ebmdatalab.iam.gserviceaccount.com GCP service account
GCP_CREDENTIALS_PATH = env.path("GCP_CREDENTIALS_PATH")

# A secret that we generate ourselves
EBMBOT_WEBHOOK_SECRET = env.str("EBMBOT_WEBHOOK_SECRET").encode("ascii")

# TTL in seconds for webhook token
EBMBOT_WEBHOOK_TOKEN_TTL = 60 * 60

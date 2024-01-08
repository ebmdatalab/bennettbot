from urllib.parse import urlparse

from ebmbot import settings
from ebmbot.logger import logger


logger.info("running ebmbot.webserver")
port = urlparse(settings.WEBHOOK_ORIGIN).port

bind = f"0.0.0.0:{port}"

workers = 8
timeout = 120

# Where to log to (stdout and stderr)
accesslog = "-"
errorlog = "-"

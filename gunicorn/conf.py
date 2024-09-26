from urllib.parse import urlparse

from bennettbot import settings
from bennettbot.logger import logger


logger.info("running bennettbot.webserver")
port = urlparse(settings.WEBHOOK_ORIGIN).port

bind = f"0.0.0.0:{port}"

workers = 8
timeout = 120

# Where to log to (stdout and stderr)
accesslog = "-"
errorlog = "-"

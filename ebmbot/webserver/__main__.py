from urllib.parse import urlparse

from .. import settings
from ..logger import logger
from . import app


logger.info("running ebmbot.webserver")
port = urlparse(settings.WEBHOOK_ORIGIN).port
app.run(host="0.0.0.0", port=port, load_dotenv=False, debug=False)

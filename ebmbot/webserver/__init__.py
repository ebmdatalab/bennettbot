from urllib.parse import urlparse

from flask import Flask

from ..logger import logger
from .. import settings
from .callback import handle_callback_webhook
from .github import handle_github_webhook

app = Flask(__name__)
app.route("/github/", methods=["POST"])(handle_github_webhook)
app.route("/callback/", methods=["POST"])(handle_callback_webhook)


if __name__ == "__main__":
    logger.info("running ebmbot.webserver")
    port = urlparse(settings.WEBHOOK_ORIGIN).port
    app.run(
        host="0.0.0.0",
        port=port,
        load_dotenv=False,
        debug=False,
    )

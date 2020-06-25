from flask import Flask

from ..logger import logger
from .. import settings
from .github import handle_github_webhook

app = Flask(__name__)
app.route("/github/", methods=["POST"])(handle_github_webhook)


if __name__ == "__main__":
    logger.info("running ebmbot.webserver")
    app.run(
        host="0.0.0.0",
        port=settings.GITHUB_WEBHOOK_PORT,
        load_dotenv=False,
        debug=False,
    )

import hmac
import json

from flask import Flask, abort, request

from . import scheduler, settings
from .logger import logger

app = Flask(__name__)


@app.route("/github/", methods=["POST"])
def handle_github_webhook():
    """Respond to webhooks from GitHub, and schedule a deploy of
    openprescribing if required.

    The webhook is configured at:

        https://github.com/ebmdatalab/openprescribing/settings/hooks/85994427
    """

    verify_signature(request)
    logger.info("Received webhook")

    if should_deploy(request):
        schedule_deploy()

    return ""


def verify_signature(request):
    """Verifiy that request has been signed correctly.

    Raises 403 if it has not been.

    See https://developer.github.com/webhooks/securing/.
    """

    secret = settings.GITHUB_WEBHOOK_SECRET
    header = request.headers.get("X-Hub-Signature")

    if header is None:
        abort(403)

    if header[:5] != "sha1=":
        abort(403)

    signature = header[5:]

    mac = hmac.new(secret, msg=request.data, digestmod="sha1")
    if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
        abort(403)


def should_deploy(request):
    """Return whether webhook is notification of merged PR."""

    data = json.loads(request.data.decode())

    if not data.get("pull_request"):
        return False

    return data["action"] == "closed" and data["pull_request"]["merged"]


def schedule_deploy():
    """Schedule a deploy of openprescribing."""

    logger.info("Scheduling deploy")
    scheduler.schedule_job("op_deploy", {}, "#general", 60)


if __name__ == "__main__":
    logger.info("running ebmbot.webserver")
    app.run(
        host="0.0.0.0",
        port=settings.GITHUB_WEBHOOK_PORT,
        load_dotenv=False,
        debug=False,
    )

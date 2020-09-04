import json

from flask import Response, abort, request

from .. import scheduler, settings
from ..job_configs import config
from ..logger import logger
from ..signatures import InvalidHMAC, validate_hmac


def handle_github_webhook(project):
    """Respond to webhooks from GitHub, and schedule a deploy of
    the relevant project if required.

    The webhook is configured at:

        https://github.com/ebmdatalab/openprescribing/settings/hooks/85994427
    """

    verify_signature(request)
    logger.info("Received webhook", project=project)

    if should_deploy(request):
        schedule_deploy(project)

    return ""


def verify_signature(request):
    """Verifiy that request has been signed correctly.

    Raises 403 if it has not been.

    See https://docs.github.com/en/developers/webhooks-and-events/securing-your-webhooks
    """

    header = request.headers.get("X-Hub-Signature")

    if header is None:
        abort(403)

    if header[:5] != "sha1=":
        abort(403)

    signature = header[5:]

    try:
        validate_hmac(
            request.data, settings.GITHUB_WEBHOOK_SECRET, signature.encode("utf8")
        )
    except InvalidHMAC:
        abort(403)


def should_deploy(request):
    """Return whether webhook is notification of merged PR."""

    data = json.loads(request.data.decode())

    if not data.get("pull_request"):
        return False

    return data["action"] == "closed" and data["pull_request"]["merged"]


def schedule_deploy(project):
    """Schedule a deploy of the given project."""

    job = f"{project}_deploy"
    if job not in config["jobs"]:
        abort(Response(f"Unknown project: {project}", 400))

    logger.info("Scheduling deploy", project=project)
    scheduler.schedule_job(job, {}, "#general", "", delay_seconds=60)

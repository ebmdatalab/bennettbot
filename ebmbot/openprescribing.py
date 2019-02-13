from threading import Thread
from dateparser import parse
from time import sleep
from datetime import datetime
import logging
import re

from slackbot.bot import respond_to
from fabric.tasks import execute

from fabfiles.openprescribing.fabfile import checkpoint
from fabfiles.openprescribing.fabfile import clear_cloudflare
from fabfiles.openprescribing.fabfile import deploy
from fabric.api import env

from ebmbot import flags

env.user = 'ebmbot'

DEPLOY_DELAY = 60

TIME_FMT = "%Y-%m-%d %H:%M"


def suppressed(func):
    def wrapper(message):
        now = datetime.now()
        if flags.deploy_suppressed:
            start_time, end_time = flags.deploy_suppressed
            if start_time <= now <= end_time:
                message.reply(
                    "Not deploying: suppressed until {}".format(
                        end_time.strftime(TIME_FMT)
                    ))
            else:
                flags.deploy_suppressed = None
                func(message)
        else:
            func(message)
    return wrapper


@suppressed
@respond_to(r'op deploy$', re.IGNORECASE)
def deploy_live_delayed(message):
    if deploy_in_progress():
        message.reply(
            "Deploy underway. Will start another when it's finished",
            in_thread=True
        )
    else:
        message.reply(
            "Deploying in {} seconds".format(DEPLOY_DELAY),
            in_thread=True
        )
    reset_or_deploy_timer(DEPLOY_DELAY, message)


@suppressed
@respond_to('op deploy now', re.IGNORECASE)
def deploy_live_now(message):
    message.reply(
        "Deploying now".format(DEPLOY_DELAY),
        in_thread=True)
    reset_or_deploy_timer(0, message)


@suppressed
@respond_to('op cancel deploy', re.IGNORECASE)
def cancel_deploy_live(message):
    reset_or_deploy_timer(None, message)
    message.reply("Cancelled", in_thread=True)


@respond_to(r'op clear cache', re.IGNORECASE)
def clear_cache(message):
    result = execute(clear_cloudflare)
    message.reply("Cache cleared:\n\n {}".format(result), in_thread=True)


@respond_to(r'op checkpoint', re.IGNORECASE)
def clear_cache(message):
    result = execute(checkpoint, False)
    message.reply(str(result), in_thread=True)


@respond_to('op cancel suppression', re.IGNORECASE)
def cancel_suppression(message):
    if flags.deploy_suppressed:
        flags.deploy_suppressed = None
        message.reply("Cancelled", in_thread=True)
    else:
        message.reply("No suppressions to cancel", in_thread=True)


@respond_to('op status', re.IGNORECASE)
def show_status(message):
    msgs = []
    if flags.deploy_suppressed:
        start_time, end_time = flags.deploy_suppressed
        msgs.append("Deploys suppressed from {} to {}`".format(
            start_time.strftime(TIME_FMT),
            end_time.strftime(TIME_FMT)))
    else:
        if flags.deploy_countdown is None:
            msgs.append("No deploys in progress")
        elif flags.deploy_countdown < 1:
            msgs.append("Deploy in progress")
        else:
            msgs.append(
                "Deploy due in {} seconds".format(flags.deploy_countdown)),
    message.reply("\n".join(msgs), in_thread=True)


@respond_to(r'op suppress from (.*) to (.*)', re.IGNORECASE)
def suppress_deploy(message, start_time, end_time):
    start_time = parse(start_time)
    end_time = parse(end_time)
    flags.deploy_suppressed = [start_time, end_time]
    message.reply(
        "Deployment suppressed from {} until {}. "
        "Cancel with `cancel suppression`".format(
            start_time.strftime(TIME_FMT),
            end_time.strftime(TIME_FMT)),
        in_thread=True
    )
    if flags.deploy_countdown:
        deploy_due_at = datetime.now() + flags.deploy_countdown
        if deploy_due_at <= end_time:
            reset_or_deploy_timer(None, message)
            message.reply("Current deployment cancelled", in_thread=True)


def deploy_timer(message):
    while flags.deploy_countdown is not None:
        if flags.deploy_countdown <= 0:
            logging.info("Starting OP deploy via fabric")
            result = execute(deploy, environment='live')
            logging.debug("Got result: %s", result)
            logging.info("Finished OP deploy via fabric")
            message.reply("Deploy done", in_thread=True)
            if flags.deploy_queued:
                flags.deploy_queued = False
                deploy_live_delayed(message)
            else:
                flags.deploy_countdown = None
        else:
            sleep(1)
            if flags.deploy_countdown is not None:
                flags.deploy_countdown -= 1


def deploy_in_progress():
    return flags.deploy_countdown in [-1, 0]


def reset_or_deploy_timer(secs, message):
    if deploy_in_progress():
        flags.deploy_queued = True
    if secs is None:
        # Cancel countdown
        flags.deploy_countdown = None
    elif flags.deploy_countdown is None:
        # Start countdown
        flags.deploy_countdown = secs
        myThread = Thread(target=deploy_timer, args=(message,))
        myThread.start()
    else:
        # Reset countdown
        flags.deploy_countdown = secs

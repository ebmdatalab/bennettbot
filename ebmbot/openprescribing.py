from threading import Thread
from dateparser import parse
from time import sleep
from datetime import datetime
import re

from slackbot.bot import respond_to
from fabric.tasks import execute

from fabfiles.openprescribing.fabfile import deploy

DEPLOY_DELAY = 60

TIME_FMT = "%Y-%m-%d %H:%M"


def suppressed(func):
    def wrapper(message):
        global deploy_suppressed
        now = datetime.now()
        if deploy_suppressed:
            start_time, end_time = deploy_suppressed
            if start_time <= now <= end_time:
                message.reply(
                    "Not deploying: suppressed until {}".format(
                        end_time.strftime(TIME_FMT)
                    ))
            else:
                deploy_suppressed = None
                func(message)
        else:
            func(message)
    return wrapper


@suppressed
@respond_to('op deploy', re.IGNORECASE)
def deploy_live_delayed(message):
    message.reply(
        "Deploying in {} seconds".format(DEPLOY_DELAY),
        in_thread=True
    )
    reset_or_deploy_timer(DEPLOY_DELAY, message)


@suppressed
@respond_to('op deploy now', re.IGNORECASE)
def deploy_live_now(message):
    reset_or_deploy_timer(0, message)


@suppressed
@respond_to('op cancel deploy', re.IGNORECASE)
def cancel_deploy_live(message):
    reset_or_deploy_timer(None, message)
    message.reply("Cancelled", in_thread=True)


@respond_to('op cancel suppression', re.IGNORECASE)
def cancel_suppression(message):
    global deploy_suppressed
    if deploy_suppressed:
        deploy_suppressed = None
        message.reply("Cancelled", in_thread=True)
    else:
        message.reply("No suppressions to cancel", in_thread=True)


@respond_to('op status', re.IGNORECASE)
def show_status(message):
    global deploy_suppressed
    global deploy_countdown
    if deploy_suppressed:
        start_time, end_time = deploy_suppressed
        msg = "Deploys suppressed {} - {}`".format(
            start_time.strftime(TIME_FMT),
            end_time.strftime(TIME_FMT)),
        message.reply(msg, in_thread=True)
    else:
        message.reply("No suppression set", in_thread=True)
        if deploy_countdown:
            message.reply(
                "Deploy due in {} seconds".format(deploy_countdown),
                in_thread=True)
        else:
            message.reply("No deploys in progress")


@respond_to('op suppress deploy(?:s) from (.*) to (.*)', re.IGNORECASE)
def suppress_deploy(message, start_time, end_time):
    global deploy_suppressed
    start_time = parse(start_time)
    end_time = parse(end_time)
    deploy_suppressed = [start_time, end_time]
    message.reply(
        "Deployment suppressed from {} until {}. "
        "Cancel with `cancel suppression`".format(
            start_time.strftime(TIME_FMT),
            end_time.strftime(TIME_FMT)),
        in_thread=True
    )
    if deploy_countdown:
        deploy_due_at = datetime.now() + deploy_countdown
        if deploy_due_at <= end_time:
            reset_or_deploy_timer(None, message)
            message.reply("Current deployment cancelled", in_thread=True)


deploy_countdown = None
deploy_suppressed = None


def deploy_timer(message):
    global deploy_countdown
    while deploy_countdown is not None:
        if deploy_countdown <= 0:
            execute(deploy, environment='live')
            message.reply("Deploy done")
            deploy_countdown = None
        else:
            sleep(1)
            if deploy_countdown is not None:
                deploy_countdown -= 1


def reset_or_deploy_timer(secs, message):
    global deploy_countdown
    if secs is None:
        # Cancel countdown
        deploy_countdown = None
    elif deploy_countdown is None:
        # Start countdown
        deploy_countdown = secs
        myThread = Thread(target=deploy_timer, args=(message,))
        myThread.start()
    else:
        # Reset countdown
        deploy_countdown = secs

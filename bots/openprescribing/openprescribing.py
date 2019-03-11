from threading import Thread
from time import sleep
from datetime import datetime
import logging
import re

from slackbot.bot import respond_to

from fabfiles.openprescribing.fabfile import clear_cloudflare
from fabfiles.openprescribing.fabfile import deploy
from fabric.api import env

from bots.openprescribing import flags
from bots.utils import safe_execute


# We store a copy of hosts after we import the fabfile, because the
# fabric env is global and thus not threadsafe
HOSTS = env.hosts[:]

DEPLOY_DELAY = 60

TIME_FMT = "%Y-%m-%d %H:%M"


def suppressed(func):
    def wrapper(message):
        now = datetime.now()
        if flags.deploy_suppressed:
            start_time, end_time = flags.deploy_suppressed
            if start_time <= now <= end_time:
                msg = ""
                if not message.body['ts']:
                    msg = "PR merged. "
                msg += "Not deploying: suppressed until {}".format(
                        end_time.strftime(TIME_FMT))
                msg += "\nIn an emergency, use `op cancel suppression` "
                msg += "followed by `op deploy` to force a deployment"
                message.reply(msg)
            else:
                flags.deploy_suppressed = None
                func(message)
        else:
            func(message)
    return wrapper


@respond_to(r'op help', re.IGNORECASE)
def op_help(message):
    msg = """
`op deploy`: deploy after a {}s delay
`op deploy now`: deploy immediately
`op cancel deploy`: cancel any pending deploy (but not a running one!)
`op clear cache`: clear cloudflare cache
`op suppress from 12:40 to 18:00`: don't allow deploys between these times
`op cancel suppression`: cancel any current suppression
`op status`: show current deployment and supression status
"""
    message.reply(msg.format(DEPLOY_DELAY))


@respond_to(r'op deploy$', re.IGNORECASE)
@suppressed
def deploy_live_delayed(message):
    if deploy_in_progress():
        message.reply(
            "Deploy underway. Will start another when it's finished")
    else:
        if message.body['ts']:
            msg = "Deploying in {} seconds".format(DEPLOY_DELAY)
            message.reply(msg)
        else:
            msg = "PR merged. "
            msg += "Deploying in {} seconds".format(DEPLOY_DELAY)
            # This was triggered from github webhooks - no thread
            msg += "Use `op cancel deploy` to prevent this"
            message.send_webapi(msg)
    reset_or_deploy_timer(DEPLOY_DELAY, message)


@respond_to('op deploy now', re.IGNORECASE)
@suppressed
def deploy_live_now(message):
    message.reply(
        "Deploying now".format(DEPLOY_DELAY))
    reset_or_deploy_timer(0, message)


@respond_to('op cancel deploy', re.IGNORECASE)
@suppressed
def cancel_deploy_live(message):
    reset_or_deploy_timer(None, message)
    message.reply("Cancelled.\nUse `op deploy` to start again.")


@respond_to(r'op clear cache', re.IGNORECASE)
def clear_cache(message):
    result = safe_execute(clear_cloudflare, hosts=HOSTS)
    message.reply("Cache cleared:\n\n {}".format(result))


@respond_to('op cancel suppression', re.IGNORECASE)
def cancel_suppression(message):
    if flags.deploy_suppressed:
        flags.deploy_suppressed = None
        message.reply("Cancelled")
    else:
        message.reply("No suppressions to cancel")


@respond_to('op status', re.IGNORECASE)
def show_status(message):
    msgs = []
    if flags.deploy_suppressed:
        start_time, end_time = flags.deploy_suppressed
        if end_time >= datetime.now():
            msgs.append("Deploys suppressed from {} to {}".format(
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
    message.reply("\n".join(msgs))


def _time_today(time_str):
    now = datetime.now()
    if len(time_str) == 4:
        hour = int(time_str[:2])
        minute = int(time_str[2:])
    else:
        hour, minute = [int(x) for x in time_str.split(':')]
    return datetime(now.year, now.month, now.day, hour, minute)


@respond_to(r'op suppress from (.*) to (.*)', re.IGNORECASE)
def suppress_deploy(message, start_time, end_time):
    start_time = _time_today(start_time)
    end_time = _time_today(end_time)
    if end_time < start_time:
        raise ValueError("End time must be after start time!")
    flags.deploy_suppressed = [start_time, end_time]
    message.reply(
        "Deployment suppressed from {} until {}. "
        "Cancel with `cancel suppression`".format(
            start_time.strftime(TIME_FMT),
            end_time.strftime(TIME_FMT))
    )
    if flags.deploy_countdown:
        deploy_due_at = datetime.now() + flags.deploy_countdown
        if deploy_due_at <= end_time:
            reset_or_deploy_timer(None, message)
            message.reply("Current deployment cancelled")


def deploy_timer(message):
    while flags.deploy_countdown is not None:
        if flags.deploy_countdown <= 0:
            logging.info("Starting OP deploy via fabric")
            try:
                safe_execute(
                    deploy, hosts=HOSTS, environment='production')
                logging.info("Finished OP deploy via fabric")
                message.reply("Deploy done")
            except Exception as e:
                message.reply(
                    "Error during deploy: {}".format(e))
                raise
            finally:
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
        timer_thread = Thread(target=deploy_timer, args=(message,))
        timer_thread.start()
    else:
        # Reset countdown
        flags.deploy_countdown = secs

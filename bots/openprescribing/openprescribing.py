from threading import Thread
from time import sleep
from datetime import date, datetime
import functools
import logging
import re

from slackbot.bot import respond_to

from fabfiles.openprescribing.fabfile import clear_cloudflare
from fabfiles.openprescribing.fabfile import deploy
from fabfiles.openprescribing.fabfile import call_management_command
from fabric.api import env

from bots.openprescribing import flags
from bots.utils import safe_execute, reply


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
                reply(message,
                    "Not deploying: suppressed until {}".format(
                        end_time.strftime(TIME_FMT)
                    ))
            else:
                flags.deploy_suppressed = None
                func(message)
        else:
            func(message)
    return wrapper


def log_call(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        logger.info(fn.__name__ + ' {')
        if args:
            logger.info("args: %r", args)
        if kwargs:
            logger.info("kwargs: %r", kwargs)
        log_flags()
        rv = fn(*args, **kwargs)
        logger.info(fn.__name__ + ' }')
        return rv
    return wrapper


@respond_to(r'op help', re.IGNORECASE)
@log_call
def op_help(message):
    msg = """
`op deploy`: deploy after a {}s delay
`op deploy now`: deploy immediately
`op cancel deploy`: cancel any pending deploy (but not a running one!)
`op clear cache`: clear cloudflare cache
`op suppress from 12:40 to 18:00`: don't allow deploys between these times
`op cancel suppression`: cancel any current suppression
`op status`: show current deployment and supression status
`op staging deploy <name>`: deploy branch <name> to staging
`op ncso import`: run NCSO concession importer
`op ncso report'`: show unreconciled NCSO concessions
`op ncso reconcile concession [id] against vmpp [id]`: reconcile concession against VMPP
`op ncso send alerts`: send alerts for NCSO concessions
"""
    reply(message, msg.format(DEPLOY_DELAY), do_log=False)


@respond_to(r'op deploy$', re.IGNORECASE)
@suppressed
@log_call
def deploy_live_delayed(message):
    if deploy_in_progress():
        reply(message,
            "Deploy underway. Will start another when it's finished")
    else:
        if message.body['ts']:
            msg = "Deploying in {} seconds".format(DEPLOY_DELAY)
            reply(message, msg)
        else:
            msg = "PR merged. "
            msg += "Deploying in {} seconds".format(DEPLOY_DELAY)
            # This was triggered from github webhooks - no thread
            message.send_webapi(msg)
    reset_or_deploy_timer(DEPLOY_DELAY, message)


@respond_to('op deploy now', re.IGNORECASE)
@suppressed
@log_call
def deploy_live_now(message):
    reply(message,
         "Deploying now".format(DEPLOY_DELAY))
    reset_or_deploy_timer(0, message)


@respond_to('op staging deploy (.*)', re.IGNORECASE)
@log_call
def deploy_branch_to_staging(message, branch):
    if flags.staging_deploy_in_progress:
        reply(message,
             "Deploy of {} already in progress. Refusing to deploy!".format(
                flags.staging_deploy_in_progress))
    else:
        try:
            reply(message, "Deploy of {} to staging started".format(branch))
            flags.staging_deploy_in_progress = branch
            safe_execute(
                deploy, hosts=HOSTS, environment='staging', branch=branch)
            reply(message, "Deploy of {} to staging finished".format(branch))
            logging.info("Deploy of {} to staging finished".format(branch))
        finally:
            flags.staging_deploy_in_progress = False


@respond_to('op cancel deploy', re.IGNORECASE)
@suppressed
@log_call
def cancel_deploy_live(message):
    reset_or_deploy_timer(None, message)
    reply(message, "Cancelled")


@respond_to(r'op clear cache', re.IGNORECASE)
@log_call
def clear_cache(message):
    result = safe_execute(clear_cloudflare, hosts=HOSTS)
    reply(message, "Cache cleared:\n\n {}".format(result))


@respond_to('op cancel suppression', re.IGNORECASE)
@log_call
def cancel_suppression(message):
    if flags.deploy_suppressed:
        flags.deploy_suppressed = None
        reply(message, "Cancelled")
    else:
        reply(message, "No suppressions to cancel")


@respond_to('op status', re.IGNORECASE)
@log_call
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
    reply(message, "\n".join(msgs))


def _time_today(time_str):
    now = datetime.now()
    if len(time_str) == 4:
        hour = int(time_str[:2])
        minute = int(time_str[2:])
    else:
        hour, minute = [int(x) for x in time_str.split(':')]
    return datetime(now.year, now.month, now.day, hour, minute)


@respond_to(r'op suppress from (.*) to (.*)', re.IGNORECASE)
@log_call
def suppress_deploy(message, start_time, end_time):
    start_time = _time_today(start_time)
    end_time = _time_today(end_time)
    if end_time < start_time:
        raise ValueError("End time must be after start time!")
    flags.deploy_suppressed = [start_time, end_time]
    reply(message,
         "Deployment suppressed from {} until {}. "
         "Cancel with `cancel suppression`".format(
             start_time.strftime(TIME_FMT),
             end_time.strftime(TIME_FMT))
    )
    if flags.deploy_countdown:
        deploy_due_at = datetime.now() + flags.deploy_countdown
        if deploy_due_at <= end_time:
            reset_or_deploy_timer(None, message)
            reply(message, "Current deployment cancelled")


def deploy_timer(message):
    while flags.deploy_countdown is not None:
        if flags.deploy_countdown <= 0:
            logging.info("Starting OP deploy via fabric")
            try:
                safe_execute(
                    deploy, hosts=HOSTS, environment='production')
                logging.info("Finished OP deploy via fabric")
                reply(message, "Deploy done")
            except Exception as e:
                reply(message,
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
    logging.info('reset_or_deploy_timer')
    log_flags()

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


@respond_to(r'op ncso import')
@log_call
def ncso_import(message):
    reply(message, 'Importing NCSO concessions')
    safe_execute(
        call_management_command,
        hosts=HOSTS,
        environment='production',
        command_name='fetch_and_import_ncso_concessions',
        args=(),
        kwargs={},
    )
    # No need to report that the command has finished, as
    # fetch_and_import_ncso_concessions reports to Slack.


@respond_to(r'op ncso report')
@log_call
def ncso_report(message):
    output = safe_execute(
        call_management_command,
        hosts=HOSTS,
        environment='production',
        command_name='summarise_ncso_concessions',
        args=(),
        kwargs={},
    )
    reply(message, output)


@respond_to(r'op ncso reconcile concession (\d+) against vmpp (\d+)')
@log_call
def ncso_reconcile(message, concession_id, vmpp_id):
    output = safe_execute(
        call_management_command,
        hosts=HOSTS,
        environment='production',
        command_name='reconcile_ncso_concession',
        args=(concession_id, vmpp_id),
        kwargs={},
    )
    reply(message, output)


@respond_to(r'op ncso send alerts')
@log_call
def ncso_send_alerts(message):
    reply(message, 'Sending NCSO concession alerts')
    today = date.today().strftime('%Y-%m-%d')
    output = safe_execute(
        call_management_command,
        hosts=HOSTS,
        environment='production',
        command_name='send_ncso_concessions_alerts',
        args=(today,),
        kwargs={},
    )
    reply(message, output)


def log_flags():
    logging.info('deploy_suppressed: %s', flags.deploy_suppressed)
    logging.info('deploy_countdown: %s', flags.deploy_countdown)
    logging.info('deploy_queued: %s', flags.deploy_queued)
    logging.info('staging_deploy_in_progress: %s', flags.staging_deploy_in_progress)

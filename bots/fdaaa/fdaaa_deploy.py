from slackbot.bot import respond_to
import re

from fabfiles.clinicaltrials_act_tracker.fabfile import update
from fabfiles.clinicaltrials_act_tracker.fabfile import send_tweet
from fabric.api import env

from bots.utils import safe_execute

# We store a copy of hosts after we import the fabfile, because the
# fabric env is global and thus not threadsafe
HOSTS = env.hosts[:]


@respond_to(r'fdaaa help', re.IGNORECASE)
def fdaaa_help(message):
    msg = """
`fdaaa update staging`: perform a scrape and load data into staging for review
`fdaaa deploy`: deploy by copying staging to live site
"""
    message.reply(msg)


@respond_to('fdaaa deploy', re.IGNORECASE)
def deploy_fdaaa(message):
    message.reply("Copying staging data to live site...")
    safe_execute(update, hosts=HOSTS, environment='live')
    message.reply("Done.")


@respond_to('fdaaa update staging', re.IGNORECASE)
def update_fdaaa_staging(message):
    message.reply("Updating staging site with data. Takes approx 2 hours.")
    safe_execute(update, hosts=HOSTS, environment='staging')
    # The code itself reports that it's finished via slack


@respond_to('fdaaa tweet', re.IGNORECASE)
def do_send_tweet(message):
    safe_execute(send_tweet, hosts=HOSTS, environment='live')
    message.reply("Tweet sent: https://twitter.com/FDAAAtracker")

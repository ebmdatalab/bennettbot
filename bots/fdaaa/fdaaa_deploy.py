from slackbot.bot import respond_to
import re

from fabfiles.clinicaltrials_act_tracker.fabfile import update
from fabfiles.clinicaltrials_act_tracker.fabfile import send_tweet
from fabric.api import env

from bots.utils import safe_execute

# We store a copy of hosts after we import the fabfile, because the
# fabric env is global and thus not threadsafe
HOSTS = env.hosts[:]


@respond_to('deploy fdaaa', re.IGNORECASE)
def deploy_fdaaa(message):
    message.reply("Copying staging data to live site...")
    safe_execute(update, hosts=HOSTS, environment='live')
    message.reply("Done.", in_thread=True)


@respond_to('update fdaaa staging', re.IGNORECASE)
def update_fdaaa_staging(message):
    message.reply("Updating staging site with data. Takes approx 2 hours.")
    safe_execute(update, hosts=HOSTS, environment='staging')
    # The code itself reports that it's finished via slack


@respond_to('tweet fdaaa', re.IGNORECASE)
def do_send_tweet(message):
    safe_execute(send_tweet, hosts=HOSTS, environment='live')
    message.reply("Tweet sent: https://twitter.com/FDAAAtracker")

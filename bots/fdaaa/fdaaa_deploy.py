from slackbot.bot import respond_to
import re

from fabfiles.clinicaltrials_act_tracker.fabfile import update
from fabfiles.clinicaltrials_act_tracker.fabfile import send_tweet
from fabric.api import env

from bots.utils import safe_execute


env.user = 'ebmbot'


@respond_to('deploy fdaaa', re.IGNORECASE)
def deploy_fdaaa(message):
    message.reply("Copying staging data to live site...")
    safe_execute(update, environment='live')
    message.reply("Done.", in_thread=True)


@respond_to('update fdaaa staging', re.IGNORECASE)
def update_fdaaa_staging(message):
    message.reply("Updating staging site with data. Takes approx 2 hours.")
    safe_execute(update, environment='staging')


@respond_to('tweet fdaaa', re.IGNORECASE)
def send_tweet(message):
    safe_execute(send_tweet, environment='live')
    message.reply("Tweet sent: https://twitter.com/FDAAAtracker")

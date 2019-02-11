"""The bot modules are listed in slackbot_settings.py

For bot commands that execute fabric commands which assume sudo, this
script should be run by a user in the `fabric` group

"""
import json
import threading

from flask import Flask, request

from slackbot import settings
from slackbot.slackclient import SlackClient
from slackbot.dispatcher import Message
from slackbot.bot import Bot

from ebmbot.openprescribing import deploy_live_delayed


app = Flask(__name__)


@app.route('/', methods=['POST'])
def handle_github_webhook():
    data = json.loads(request.data)
    should_deploy = data['action'] == 'closed' and data['merged'] == 'true'
    if should_deploy:
        msg = {'channel': '#tech', 'ts': None}
        client = SlackClient(settings.API_TOKEN)
        message = Message(client, msg)
        deploy_live_delayed(message)
    return ""


def main():
    bot = Bot()
    bot.run()


if __name__ == "__main__":
    # We are warned not to use this in a production environment,
    # but I think we should be OK in this case...
    threading.Thread(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': settings.GITHUB_WEBHOOK_PORT,
        'load_dotenv': False,
        'debug': False,
        'threaded': True
    }).start()
    main()

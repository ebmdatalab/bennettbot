"""The bot modules are listed in slackbot_settings.py

For bot commands that execute fabric commands which assume sudo, this
script should be run by a user in the `fabric` group

"""
import hmac
import logging
import json
import threading

from flask import Flask, request, abort

from slackbot import settings
from slackbot.slackclient import SlackClient
from slackbot.dispatcher import Message
from slackbot.bot import Bot

from bots.openprescribing.openprescribing import deploy_live_delayed


app = Flask(__name__)


def verify_signature(request):
    # See https://developer.github.com/webhooks/securing/
    secret = settings.GITHUB_WEBOOK_SECRET
    header_signature = request.headers.get('X-Hub-Signature')
    if header_signature is None:
        abort(403)
    sha_name, signature = header_signature.split('=')
    if sha_name != 'sha1':
        abort(501)
    mac = hmac.new(secret, msg=request.data, digestmod='sha1')
    if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
        abort(403)


@app.route('/github/', methods=['POST'])
def handle_github_webhook():
    logging.info("Received data %s", request.data)
    verify_signature(request)
    data = json.loads(request.data.decode())
    action = data.get('action', None)
    merged = data.get('pull_request', {}).get("merged", None)
    should_deploy = action == 'closed' and merged
    if should_deploy:
        msg = {'channel': '#technoise', 'ts': None}
        client = SlackClient(settings.API_TOKEN)
        message = Message(client, msg)
        logging.info("Triggering delayed deploy")
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

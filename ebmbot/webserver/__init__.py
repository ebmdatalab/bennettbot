from flask import Flask

from .github import handle_github_webhook


def check():
    return "ok"


app = Flask(__name__)
app.route("/check/", methods=["GET"])(check)
app.route("/github/<project>/", methods=["POST"])(handle_github_webhook)

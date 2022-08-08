import os

from . import settings

from slack_bolt import App, BoltResponse
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.error import BoltUnhandledRequestError


# Initializes your app with your bot token and socket mode handler
app = App(
    token=settings.SLACK_APP_TOKEN,  
    signing_secret=settings.SLACK_SIGNING_SECRET,   
    # enable @app.error handler to catch the patterns
    raise_error_for_unhandled_request=True,
)


@app.error
def handle_errors(error):
    if isinstance(error, BoltUnhandledRequestError):
        # you may want to have some logging here
        return BoltResponse(status=200, body="")
    else:
        # other error patterns
        return BoltResponse(status=500, body="Something Wrong")

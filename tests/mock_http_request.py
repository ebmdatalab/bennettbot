import json
from urllib.parse import parse_qs

from mocket import Mocket
from mocket.mockhttp import Entry

from .time_helpers import TS


USERS = {
    # bot
    "U1234": {
        "name": "test_username",
        "id": "U1234",
        "is_restricted": False,
        "is_bot": True,
    },
    # internal (unrestricted) user
    "UINT": {
        "name": "test_user",
        "id": "UINT",
        "is_restricted": False,
        "is_bot": False,
    },
    # guest user
    "UGUEST": {
        "name": "test_guest",
        "id": "UGUEST",
        "is_restricted": True,
        "is_bot": False,
    },
    # new (joined after mock app is started up)
    "NEWINT": {
        "name": "test_new_internal",
        "id": "NEWINT",
        "is_restricted": False,
        "is_bot": False,
    },
    "NEWGUEST": {
        "name": "test_new_guest",
        "id": "NEWGUEST",
        "is_restricted": True,
        "is_bot": False,
    },
}


def mocket_register(responses_dict):
    """
    A helper to register slack URIs
    Called with a dict of endpoints and mock response json:
    {
        <endpoint_fragment>: [list of dicts representing expected response json]
    }

    e.g.
    {
        "chat.postMessage": [{"ok": True, "ts": "12345.678",}]
    }

    Note: if only one response is given and the endpoint/method is called multiple
    times, that response will be returned each time. Multiple responses can be provided
    if the endpoint/method will be called multiple times and is expected to return
    a different response each time.
    """
    for endpoint, responses in responses_dict.items():
        Entry.register(
            Entry.POST,
            f"https://slack.com/api/{endpoint}",
            *[json.dumps(response) for response in responses],
        )


def register_bot_uris():
    """
    Register (nearly) all the uris needed to start and run the bot
    The exception is users.info, which is called for a specific user in
    order to check if they are an internal or guest user.

    Tests that need this method will need to register it themselves in order
    to ensure it returns the expected user(s).
    """
    mocket_register(
        {
            # authenticate
            "auth.test": [{"ok": True}],
            # get all the channels
            "conversations.list": [
                {
                    "ok": True,
                    "channels": [
                        {"name": "bennettadmins", "id": "C0000", "is_archived": False},
                        {"name": "techsupport", "id": "C0001", "is_archived": False},
                        {"name": "channel", "id": "C0002", "is_archived": False},
                        {"name": "channel1", "id": "C0003", "is_archived": False},
                        {
                            "name": "archived-channel",
                            "id": "C0004",
                            "is_archived": True,
                        },
                    ],
                }
            ],
            # get all users (called to find bot's id)
            "users.list": [
                {
                    "ok": True,
                    "members": [
                        user
                        for user_id, user in USERS.items()
                        if user_id.startswith("U")
                    ],
                }
            ],
            # called to find out if bot is in channel
            "conversations.members": [
                # mock bot membership of one channel
                {"ok": True, "members": ["U1234"]},
                {"ok": True, "members": []},
            ],
            # join channels bot isn't already in
            "conversations.join": [{"ok": True}],
            # react to posts
            "reactions.add": [{"ok": True}],
            # post messages
            "chat.postMessage": [{"ok": True, "ts": TS, "channel": "channel"}],
            # get a URL to repost (from a failed job, to tech-suport)
            "chat.getPermalink": [
                {"ok": True, "channel": "channel", "permalink": "http://example.com"}
            ],
        },
    )


def register_dispatcher_uris():
    """
    Register (nearly) all the uris needed for dispatcher methods.
    The response to a job is typically to add a reaction and then report
    the output or to report success. If a job fails, it will also call
    getPermalink to get the message's URL in order to report to tech-support.
    """
    mocket_register(
        {
            "chat.postMessage": [{"ok": True, "ts": TS, "channel": "channel"}],
            "chat.getPermalink": [
                {"ok": True, "channel": "channel", "permalink": "http://example.com"}
            ],
            "reactions.add": [{"ok": True}],
        }
    )


def get_mock_received_requests():
    """
    Return a dict of {apipath: body} for each request received by
    mocket.
    Note that the slack_sdk uses params for its api calls for most methods.
    It uses json for calls that use (or can use) blocks. For our purposes, this
    if just the chat.postMessage calls.
    param values are converted to lists during the api call, so e.g. for a
    reactions.add call, a call using
        client.reactions_add(channel="C1", name=":sos:", timestamp=123.45)
    sends the request with:
        {"channel": ["C1"], "name": [":sos:"], "timestamp": ["123.45"]}
    e.g.
    https://github.com/slackapi/python-slack-sdk/blob/c47ea206491ca3e0be48749169041cf84925acd0/slack_sdk/web/client.py#L2709
    """
    requests_by_path = {}
    for request in Mocket.request_list():
        if request.headers["content-length"] == "0":
            body = ""
        elif request.path == "/api/chat.postMessage":
            body = json.loads(request.body)
        else:
            body = parse_qs(request.body)
        requests_by_path.setdefault(request.path, []).append(body)
    return requests_by_path

"""
Based on https://github.com/slackapi/bolt-python/blob/v1.14.3/tests/mock_web_api_server.py
"""
import json
import logging
import threading
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional, Type
from urllib.parse import ParseResult, parse_qs, urlparse


class MockHandler(SimpleHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    default_request_version = "HTTP/1.1"
    logger = logging.getLogger(__name__)
    received_requests = {}
    received_requests_kwargs = {}

    def is_valid_token(self):
        return "Authorization" in self.headers and str(
            self.headers["Authorization"]
        ).startswith("Bearer xoxb-")

    def is_valid_user_token(self):
        return "Authorization" in self.headers and str(
            self.headers["Authorization"]
        ).startswith("Bearer xoxp-")

    def set_common_headers(self):
        self.send_header("content-type", "application/json;charset=utf-8")
        self.send_header("connection", "close")
        self.end_headers()

    invalid_auth = {
        "ok": False,
        "error": "invalid_auth",
    }

    oauth_v2_access_response = """
{
    "ok": true,
    "access_token": "xoxb-17653672481-19874698323-pdFZKVeTuE8sk7oOcBrzbqgy",
    "token_type": "bot",
    "scope": "chat:write,commands",
    "bot_user_id": "U0KRQLJ9H",
    "app_id": "A0KRD7HC3",
    "team": {
        "name": "Slack Softball Team",
        "id": "T9TK3CUKW"
    },
    "enterprise": {
        "name": "slack-sports",
        "id": "E12345678"
    },
    "authed_user": {
        "id": "U1234",
        "scope": "chat:write",
        "access_token": "xoxp-1234",
        "token_type": "user"
    }
}
"""
    oauth_v2_access_bot_refresh_response = """
    {
        "ok": true,
        "app_id": "A0KRD7HC3",
        "access_token": "xoxb-valid-refreshed",
        "expires_in": 43200,
        "refresh_token": "xoxe-1-valid-bot-refreshed",
        "token_type": "bot",
        "scope": "chat:write,commands",
        "bot_user_id": "U0KRQLJ9H",
        "team": {
            "name": "Slack Softball Team",
            "id": "T9TK3CUKW"
        },
        "enterprise": {
            "name": "slack-sports",
            "id": "E12345678"
        }
    }
"""
    oauth_v2_access_user_refresh_response = """
        {
            "ok": true,
            "app_id": "A0KRD7HC3",
            "access_token": "xoxp-valid-refreshed",
            "expires_in": 43200,
            "refresh_token": "xoxe-1-valid-user-refreshed",
            "token_type": "user",
            "scope": "search:read",
            "team": {
                "name": "Slack Softball Team",
                "id": "T9TK3CUKW"
            },
            "enterprise": {
                "name": "slack-sports",
                "id": "E12345678"
            }
        }
    """
    bot_auth_test_response = """
{
    "ok": true,
    "url": "https://subarachnoid.slack.com/",
    "team": "Subarachnoid Workspace",
    "user": "bot",
    "team_id": "T0G9PQBBK",
    "user_id": "W23456789",
    "bot_id": "BZYBOTHED"
}
"""

    user_auth_test_response = """
{
    "ok": true,
    "url": "https://subarachnoid.slack.com/",
    "team": "Subarachnoid Workspace",
    "user": "some-user",
    "team_id": "T0G9PQBBK",
    "user_id": "W99999"
}
"""
    path_responses = {
        "/webhook": "OK".encode("utf-8"),
        "/users.list": json.dumps(
            {
                "ok": True,
                "members": [
                    {"name": "test_username", "id": "U1234"},
                ],
            }
        ).encode("utf-8"),
        "/conversations.list": json.dumps(
            {
                "ok": True,
                "channels": [
                    {"name": "techsupport", "id": "C0001", "is_archived": False},
                    {"name": "channel", "id": "C0002", "is_archived": False},
                    {"name": "channel1", "id": "C0003", "is_archived": False},
                    {"name": "archived-channel", "id": "C0004", "is_archived": True},
                ],
            }
        ).encode("utf-8"),
        "/conversations.members": json.dumps({"ok": True, "members": []}).encode(
            "utf-8"
        ),
        "/conversations.join": json.dumps({"ok": True}).encode("utf-8"),
        "/chat.getPermalink": json.dumps(
            {"ok": True, "permalink": "http://test"}
        ).encode("utf-8"),
        "/chat.postMessage": json.dumps(
            {"ok": True, "channel": "C0002", "ts": 1234.0}
        ).encode("utf-8"),
        "/reactions.add": json.dumps({"ok": True}).encode("utf-8"),
    }

    def _handle(self):
        parsed_path: ParseResult = urlparse(self.path)
        path = parsed_path.path
        self.received_requests[path] = self.received_requests.get(path, 0) + 1

        request_body = self._parse_request_body(
            parsed_path=parsed_path,
            content_len=int(self.headers.get("Content-Length") or 0),
        )
        self.received_requests_kwargs.setdefault(path, []).append(request_body)

        try:
            body = None

            if path == "/received_requests.json":
                body = json.dumps(self.received_requests).encode("utf-8")
            elif (
                path == "/conversations.members" and request_body["channel"] == "C0001"
            ):
                # Mock channel members responses to simulate existing membership of one channel
                body = json.dumps({"ok": True, "members": ["U1234"]}).encode("utf-8")
            else:
                body = self.path_responses.get(path)

            if body is not None:
                self.send_response(200)
                self.set_common_headers()
                self.wfile.write(body)
                return

            if path == "/oauth.v2.access":
                if self.headers.get("authorization") is not None:
                    request_body = self._parse_request_body(
                        parsed_path=parsed_path,
                        content_len=int(self.headers.get("Content-Length") or 0),
                    )
                    self.logger.info(f"request body: {request_body}")

                    if request_body.get("grant_type") == "refresh_token":
                        refresh_token = request_body.get("refresh_token")
                        if refresh_token is not None:
                            if "bot-valid" in refresh_token:
                                self.send_response(200)
                                self.set_common_headers()
                                body = self.oauth_v2_access_bot_refresh_response
                                self.wfile.write(body.encode("utf-8"))
                                return
                            if "user-valid" in refresh_token:
                                self.send_response(200)
                                self.set_common_headers()
                                body = self.oauth_v2_access_user_refresh_response
                                self.wfile.write(body.encode("utf-8"))
                                return
                    elif request_body.get("code") is not None:
                        self.send_response(200)
                        self.set_common_headers()
                        self.wfile.write(self.oauth_v2_access_response.encode("utf-8"))
                        return

            if self.is_valid_user_token():
                if path == "/auth.test":
                    self.send_response(200)
                    self.set_common_headers()
                    self.wfile.write(self.user_auth_test_response.encode("utf-8"))
                    return

            if self.is_valid_token():
                if path == "/auth.test":
                    self.send_response(200)
                    self.set_common_headers()
                    self.wfile.write(self.bot_auth_test_response.encode("utf-8"))
                    return

                request_body = self._parse_request_body(
                    parsed_path=parsed_path,
                    content_len=int(self.headers.get("Content-Length") or 0),
                )
                self.logger.info(f"request: {path} {request_body}")

                header = self.headers["authorization"]
                pattern = str(header).split("xoxb-", 1)[1]
                if pattern.isnumeric():
                    self.send_response(int(pattern))
                    self.set_common_headers()
                    self.wfile.write("""{"ok":false}""".encode("utf-8"))
                    return
            else:
                body = self.invalid_auth

            self.send_response(HTTPStatus.OK)
            self.set_common_headers()
            self.wfile.write(json.dumps(body).encode("utf-8"))
            self.wfile.close()

        except Exception as e:
            self.logger.error(str(e), exc_info=True)
            raise

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def _parse_request_body(self, parsed_path: str, content_len: int) -> Optional[dict]:
        post_body = self.rfile.read(content_len)
        request_body = None
        if post_body:
            try:
                post_body = post_body.decode("utf-8")
                if post_body.startswith("{"):
                    request_body = json.loads(post_body)
                else:
                    request_body = {k: v[0] for k, v in parse_qs(post_body).items()}
            except UnicodeDecodeError:
                pass
        else:
            if parsed_path and parsed_path.query:
                request_body = {k: v[0] for k, v in parse_qs(parsed_path.query).items()}
        return request_body


class MockServerThread(threading.Thread):
    def __init__(self, recorder, handler: Type[SimpleHTTPRequestHandler] = MockHandler):
        threading.Thread.__init__(self)
        self.handler = handler
        # recorder is just a Mock() object that keeps track of things that happen on this
        # mock server, and which we can use to make assertions about calls made
        self.recorder = recorder

    def run(self):
        self.server = HTTPServer(("localhost", 8888), self.handler)
        self.recorder.mock_received_requests = self.handler.received_requests
        self.recorder.mock_received_requests_kwargs = (
            self.handler.received_requests_kwargs
        )
        self.recorder.server_url = "http://localhost:8888"
        self.recorder.host, self.recorder.port = self.server.socket.getsockname()
        self.recorder.server_started.set()  # threading.Event()

        self.recorder = None
        try:
            self.server.serve_forever(0.05)
        finally:
            self.server.server_close()

    def stop(self):
        self.handler.received_requests = {}
        self.handler.received_requests_kwargs = {}
        self.server.shutdown()
        self.join()


def setup_mock_web_api_server(mock_recorder):
    mock_recorder.server_started = threading.Event()
    mock_recorder.thread = MockServerThread(mock_recorder)
    mock_recorder.thread.start()
    mock_recorder.server_started.wait()


def cleanup_mock_web_api_server(mock_recorder):
    mock_recorder.thread.stop()
    mock_recorder.thread = None

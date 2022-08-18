"""
Configuration for pytest.
"""

import os
from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from slack_bolt import App
from slack_sdk import WebClient

from ebmbot import settings

from .mock_web_api_server import cleanup_mock_web_api_server, setup_mock_web_api_server


pytest.register_assert_rewrite("tests.assertions")


@pytest.fixture(autouse=True)
def reset_db():
    try:
        os.remove(settings.DB_PATH)
    except FileNotFoundError:
        pass


@dataclass
class MockRecordingClient:
    client: WebClient
    recorder: Mock


@dataclass
class MockRecordingApp:
    app: App
    recorder: Mock


@pytest.fixture
def mock_client():
    test_recorder = Mock()
    setup_mock_web_api_server(test_recorder)
    mock_api_server_base_url = "http://localhost:8888"

    yield MockRecordingClient(
        client=WebClient(
            token="xoxb-valid",
            base_url=mock_api_server_base_url,
        ),
        recorder=test_recorder,
    )
    cleanup_mock_web_api_server(test_recorder)


@pytest.fixture
def mock_app(mock_client):
    yield MockRecordingApp(
        app=App(client=mock_client.client, raise_error_for_unhandled_request=True),
        recorder=mock_client.recorder,
    )

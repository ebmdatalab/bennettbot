import pytest

from ebmbot import webserver


@pytest.fixture()
def web_client():
    return webserver.app.test_client()

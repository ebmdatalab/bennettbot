import pytest

from bennettbot import webserver


@pytest.fixture()
def web_client():
    return webserver.app.test_client()

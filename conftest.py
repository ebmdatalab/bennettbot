"""Configuration for pytest.
"""

import os
import sys

import pytest

from ebmbot import settings

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ebmbot"))

pytest.register_assert_rewrite("tests.assertions")


@pytest.fixture(autouse=True)
def reset_db():
    try:
        os.remove(settings.DB_PATH)
    except FileNotFoundError:
        pass

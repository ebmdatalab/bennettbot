import json
from datetime import datetime

from workspace.standup.jobs import daily_rota, get_weekday_date, weekly_rota


def test_weekly_rota_odd_week(freezer):
    freezer.move_to("2024-12-05")
    assert json.loads(weekly_rota()) == [
        {
            "text": {"text": "Team Rex stand ups this week", "type": "plain_text"},
            "type": "header",
        },
        {
            "text": {
                "text": "Monday: Jon (backup: Mike)\nWednesday: Steve (backup: Mary)\nFriday: Katie (backup: Thomas)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]


def test_weekly_rota_even_week(freezer):
    freezer.move_to("2024-12-09")
    assert json.loads(weekly_rota()) == [
        {
            "text": {"text": "Team Rex stand ups this week", "type": "plain_text"},
            "type": "header",
        },
        {
            "text": {
                "text": "Monday: Mike (backup: Jon)\nWednesday: Mary (backup: Steve)\nFriday: Thomas (backup: Katie)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]


def test_daily_rota_odd_week(freezer):
    freezer.move_to("2024-12-16")
    assert json.loads(daily_rota("monday")) == [
        {
            "text": {"text": "Team Rex stand up", "type": "plain_text"},
            "type": "header",
        },
        {
            "text": {
                "text": "Monday: Jon (backup: Mike)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]


def test_daily_rota_even_week(freezer):
    freezer.move_to("2024-12-09")
    assert json.loads(daily_rota("wednesday")) == [
        {
            "text": {"text": "Team Rex stand up", "type": "plain_text"},
            "type": "header",
        },
        {
            "text": {
                "text": "Wednesday: Mary (backup: Steve)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]


def test_get_weekday_date(freezer):
    freezer.move_to("2024-12-10")  # Tuesday
    assert get_weekday_date("monday") == datetime(2024, 12, 16).date()
    assert get_weekday_date("wednesday") == datetime(2024, 12, 11).date()
    assert get_weekday_date("friday") == datetime(2024, 12, 13).date()

    freezer.move_to("2024-12-12")  # Thursday
    assert get_weekday_date("monday") == datetime(2024, 12, 16).date()
    assert get_weekday_date("wednesday") == datetime(2024, 12, 18).date()
    assert get_weekday_date("friday") == datetime(2024, 12, 13).date()

    freezer.move_to("2024-12-15")  # Sunday
    assert get_weekday_date("monday") == datetime(2024, 12, 16).date()
    assert get_weekday_date("wednesday") == datetime(2024, 12, 18).date()
    assert get_weekday_date("friday") == datetime(2024, 12, 20).date()

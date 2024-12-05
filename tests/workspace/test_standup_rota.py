import json

from workspace.standup.jobs import weekly_rota


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

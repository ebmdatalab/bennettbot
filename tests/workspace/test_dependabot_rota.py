import json

from workspace.dependabot.jobs import report_rota
from workspace.utils.people import People


TEAM_REX = [People.JON, People.LUCY, People.KATIE]


def test_rota_report_on_monday(freezer, monkeypatch):
    freezer.move_to("2024-03-25")
    monkeypatch.setattr("workspace.dependabot.jobs.TEAM_REX", TEAM_REX)

    blocks = json.loads(report_rota())

    assert blocks == [
        {"text": {"text": "Dependabot rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "To review dependabot PRs this week (25 Mar-29 Mar): <@U035FT48KEK>",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "To review dependabot PRs next week (01 Apr-05 Apr): Jon",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]


def test_rota_report_on_tuesday(freezer, monkeypatch):
    freezer.move_to("2024-03-26")
    monkeypatch.setattr("workspace.dependabot.jobs.TEAM_REX", TEAM_REX)

    blocks = json.loads(report_rota())

    assert blocks == [
        {"text": {"text": "Dependabot rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "To review dependabot PRs this week (25 Mar-29 Mar): <@U035FT48KEK>",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "To review dependabot PRs next week (01 Apr-05 Apr): Jon",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]

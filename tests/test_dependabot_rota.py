import csv
import json
from unittest.mock import patch

from workspace.dependabot.jobs import report_rota


@patch("workspace.dependabot.jobs.get_rota_data_from_sheet")
def test_rota_report_on_monday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2024-03-25")
    with open("tests/workspace/dependabot-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {"text": {"text": "Dependabot rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "To review dependabot PRs this week: Lucy",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]


@patch("workspace.dependabot.jobs.get_rota_data_from_sheet")
def test_rota_report_on_monday_with_no_future_dates(get_rota_data_from_sheet, freezer):
    freezer.move_to("2024-10-07")
    with open("tests/workspace/dependabot-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {"text": {"text": "Dependabot rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "No rota data found for this week",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]


@patch("workspace.dependabot.jobs.get_rota_data_from_sheet")
def test_rota_report_on_tuesday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2023-07-25")
    with open("tests/workspace/dependabot-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {"text": {"text": "Dependabot rota", "type": "plain_text"}, "type": "header"},
    ]

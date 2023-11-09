import csv
import json
from unittest.mock import patch

from workspace.outputchecking.jobs import report_rota


@patch("workspace.outputchecking.jobs.get_rota_data_from_sheet")
def test_rota_report_on_monday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2023-02-20")
    with open("tests/workspace/output-checking-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {"text": {"text": "Tech support rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "Lead reviewer this week: Louis Fisher (secondary: Colm Andrews)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "Lead reviewer next week: Jon Massey (secondary: Lisa Hopcroft)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]


@patch("workspace.outputchecking.jobs.get_rota_data_from_sheet")
def test_rota_report_on_tuesday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2023-02-21")
    with open("tests/workspace/output-checking-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {"text": {"text": "Tech support rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "Lead reviewer next week: Jon Massey (secondary: Lisa Hopcroft)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]

import csv
import json
from unittest.mock import patch

from workspace.techsupport.jobs import report_rota


@patch("workspace.techsupport.jobs.get_rota_data_from_sheet")
def test_rota_report_on_monday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2023-07-24")
    with open("tests/workspace/tech-support-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {"text": {"text": "Tech support rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "Primary tech support this week: Iain (secondary: Peter, Steve)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "Primary tech support next week: Ben (secondary: Becky)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]


@patch("workspace.techsupport.jobs.get_rota_data_from_sheet")
def test_rota_report_on_tuesday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2023-07-25")
    with open("tests/workspace/tech-support-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {"text": {"text": "Tech support rota", "type": "plain_text"}, "type": "header"},
        {
            "text": {
                "text": "Primary tech support next week: Ben (secondary: Becky)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
    ]

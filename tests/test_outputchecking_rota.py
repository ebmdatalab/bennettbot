import csv
import json
from unittest.mock import patch

from workspace.outputchecking.jobs import report_rota


@patch(
    "workspace.outputchecking.jobs.OutputCheckingRotaReporter.get_rota_data_from_sheet"
)
def test_rota_report_on_monday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2023-02-20")
    with open("tests/workspace/output-checking-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {
            "text": {"text": "Output checking rota", "type": "plain_text"},
            "type": "header",
        },
        {
            "text": {
                "text": "Lead reviewer this week (20 Feb-24 Feb): Louis Fisher (secondary: Colm Andrews)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "Lead reviewer next week (27 Feb-03 Mar): Jon Massey (secondary: Lisa Hopcroft)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://docs.google.com/spreadsheets/d/1i3D_HtuYUCU_dqvRug94YkfK6pG4ECyxTdOangubUlY|Open rota spreadsheet>",
            },
        },
    ]


@patch(
    "workspace.outputchecking.jobs.OutputCheckingRotaReporter.get_rota_data_from_sheet"
)
def test_rota_report_on_tuesday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2023-02-21")
    with open("tests/workspace/output-checking-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {
            "text": {"text": "Output checking rota", "type": "plain_text"},
            "type": "header",
        },
        {
            "text": {
                "text": "Lead reviewer this week (20 Feb-24 Feb): Louis Fisher (secondary: Colm Andrews)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "Lead reviewer next week (27 Feb-03 Mar): Jon Massey (secondary: Lisa Hopcroft)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://docs.google.com/spreadsheets/d/1i3D_HtuYUCU_dqvRug94YkfK6pG4ECyxTdOangubUlY|Open rota spreadsheet>",
            },
        },
    ]


@patch(
    "workspace.outputchecking.jobs.OutputCheckingRotaReporter.get_rota_data_from_sheet"
)
def test_rota_report_missing_future_dates(get_rota_data_from_sheet, freezer):
    freezer.move_to("2024-01-08")
    with open("tests/workspace/output-checking-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {
            "text": {"text": "Output checking rota", "type": "plain_text"},
            "type": "header",
        },
        {
            "text": {
                "text": "No rota data found for this week",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "No rota data found for next week",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://docs.google.com/spreadsheets/d/1i3D_HtuYUCU_dqvRug94YkfK6pG4ECyxTdOangubUlY|Open rota spreadsheet>",
            },
        },
    ]

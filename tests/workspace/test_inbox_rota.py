import csv
import json
from unittest.mock import patch

from workspace.inbox.jobs import report_rota


@patch("workspace.inbox.jobs.InboxRotaReporter.get_rota_data_from_sheet")
def test_rota_report_on_monday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2025-03-10")
    with open("tests/workspace/inbox-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {
            "text": {"text": "Inbox rota (team@opensafely.org)", "type": "plain_text"},
            "type": "header",
        },
        {
            "text": {
                "text": "Researcher this week (10 Mar-14 Mar): PersonA",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "Researcher next week (17 Mar-21 Mar): PersonB",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://docs.google.com/spreadsheets/d/1Z50ektmaOV-H78sC__hmyH2l5HAmPsIslZYYUfT3UWU|Open rota spreadsheet>",
            },
        },
    ]


@patch("workspace.inbox.jobs.InboxRotaReporter.get_rota_data_from_sheet")
def test_rota_report_on_tuesday(get_rota_data_from_sheet, freezer):
    freezer.move_to("2025-03-11")
    with open("tests/workspace/inbox-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {
            "text": {"text": "Inbox rota (team@opensafely.org)", "type": "plain_text"},
            "type": "header",
        },
        {
            "text": {
                "text": "Researcher this week (10 Mar-14 Mar): PersonA",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {
                "text": "Researcher next week (17 Mar-21 Mar): PersonB",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://docs.google.com/spreadsheets/d/1Z50ektmaOV-H78sC__hmyH2l5HAmPsIslZYYUfT3UWU|Open rota spreadsheet>",
            },
        },
    ]


@patch("workspace.inbox.jobs.InboxRotaReporter.get_rota_data_from_sheet")
def test_rota_report_missing_future_dates(get_rota_data_from_sheet, freezer):
    freezer.move_to("2026-01-08")
    with open("tests/workspace/inbox-rota.csv") as f:
        get_rota_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(report_rota())
    assert blocks == [
        {
            "text": {"text": "Inbox rota (team@opensafely.org)", "type": "plain_text"},
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
                "text": "<https://docs.google.com/spreadsheets/d/1Z50ektmaOV-H78sC__hmyH2l5HAmPsIslZYYUfT3UWU|Open rota spreadsheet>",
            },
        },
    ]

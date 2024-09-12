import json
from datetime import date, timedelta
from os import environ

from apiclient import discovery
from google.oauth2 import service_account


outputchecking_rota_spreadsheet_id = "1i3D_HtuYUCU_dqvRug94YkfK6pG4ECyxTdOangubUlY"


def format_week(monday: date):
    friday = monday + timedelta(days=4)  # Work week
    return f"{monday.strftime("%d %b")}-{friday.strftime("%d %b")}"


def get_rota_block_for_week(rota: dict, monday: date, this_or_next: str):
    try:
        primary, secondary = rota[str(monday)]
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Lead reviewer {this_or_next} week ({format_week(monday)}): {primary} (secondary: {secondary})",
            },
        }
    except KeyError:
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"No rota data found for {this_or_next} week",
            },
        }


def get_block_linking_rota_spreadsheet(spreadsheet_id):
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"<https://docs.google.com/spreadsheets/d/{spreadsheet_id}|Open rota spreadsheet>",
        },
    }


def report_rota():
    rows = get_rota_data_from_sheet()
    rota = {row[0]: (row[1], row[2]) for row in rows[1:] if len(row) >= 3}
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Output checking rota",
            },
        },
    ]
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    blocks.append(get_rota_block_for_week(rota, this_monday, this_or_next="this"))

    next_monday = this_monday + timedelta(days=7)
    blocks.append(get_rota_block_for_week(rota, next_monday, this_or_next="next"))
    blocks.append(
        get_block_linking_rota_spreadsheet(outputchecking_rota_spreadsheet_id)
    )
    return json.dumps(blocks, indent=2)


def get_rota_data_from_sheet():  # pragma: no cover
    credentials = service_account.Credentials.from_service_account_file(
        environ["GCP_CREDENTIALS_PATH"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = discovery.build("sheets", "v4", credentials=credentials)
    return (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=outputchecking_rota_spreadsheet_id,
            range="Rota 2024",
        )
        .execute()
    )["values"]


if __name__ == "__main__":
    print(report_rota())

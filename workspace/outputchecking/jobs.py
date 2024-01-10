import json
from datetime import date, timedelta
from os import environ

from apiclient import discovery
from google.oauth2 import service_account


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
    if today.weekday() == 0:  # Monday
        if str(today) in rota:
            primary, secondary = rota[str(today)]
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Lead reviewer this week: {primary} (secondary: {secondary})",
                    },
                }
            )
        else:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "No rota data found for this week",
                    },
                }
            )

    next_monday = str(today + timedelta(7 - today.weekday()))
    if next_monday in rota:
        primary, secondary = rota[next_monday]
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Lead reviewer next week: {primary} (secondary: {secondary})",
                },
            }
        )
    else:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "No rota data found for next week",
                },
            }
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
            spreadsheetId="1i3D_HtuYUCU_dqvRug94YkfK6pG4ECyxTdOangubUlY",
            range="Rota 2024",
        )
        .execute()
    )["values"]


if __name__ == "__main__":
    print(report_rota())

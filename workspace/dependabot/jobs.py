import json
from datetime import date
from os import environ

from apiclient import discovery
from google.oauth2 import service_account


def report_rota():
    rows = get_rota_data_from_sheet()
    rota = {row[0]: row[1] for row in rows[1:]}

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Dependabot rota",
            },
        },
    ]

    today = date.today()
    if today.weekday() == 0:  # Monday
        if str(today) in rota:
            checker = rota[str(today)]
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"To review dependabot PRs this week: {checker}",
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
            spreadsheetId="1mxAks8tfVEBTSarKoNREsdztW3bTqvIPgV-83GY6CFU",
            range="Rota",
        )
        .execute()
    )["values"]


if __name__ == "__main__":
    print(report_rota())

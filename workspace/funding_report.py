import json
from datetime import date, datetime

from apiclient import discovery
from google.oauth2 import service_account

from ebmbot import settings


def main():
    rows = get_data_from_sheet()

    headers = rows[0]
    rows = [dict(zip(headers, row)) for row in rows[1:]]

    calls_recently_added = []
    calls_closing_soon = []

    for row in rows:
        opportunity = row["Opportunity"]
        funder = row["Funder(s)"]
        type_ = row["Type"]
        link = row["Link (specific call)"] or row["Link (general funding stream)"]

        award = row["Max award (£)"]
        if not award.strip():  # pragma: no cover
            award = "£ Not stated"
        elif award.isnumeric():  # pragma: no cover
            award = f"£{int(award):,}"

        added_date = row["Added date"]
        if not added_date:  # pragma: no cover
            continue
        added_date = datetime.strptime(added_date, "%d %b %Y").date()
        days_since_added = (date.today() - added_date).days

        deadline_date = row["Deadline date"]
        if not deadline_date:  # pragma: no cover
            continue
        deadline_date = datetime.strptime(deadline_date, "%d %b %Y").date()
        days_to_deadline = (deadline_date - date.today()).days

        if days_since_added <= 14:  # pragma: no branch
            line = f"{type_}: <{link}|{opportunity}>, ({funder}, {award})"
            calls_recently_added.append(
                {
                    "type": type_,
                    "deadline_date": deadline_date,
                    "line": line,
                }
            )

        if days_to_deadline <= 30:  # pragma: no branch
            line = f"{type_}: <{link}|{opportunity}>, ({funder}, {award}), closing {deadline_date} ({days_to_deadline} days)"
            calls_closing_soon.append(
                {
                    "type": type_,
                    "deadline_date": deadline_date,
                    "line": line,
                }
            )

    types = ["Project", "Programme", "Fellowship", "Other"]

    calls_recently_added.sort(
        key=lambda row: (types.index(row["type"]), row["deadline_date"])
    )
    calls_closing_soon.sort(
        key=lambda row: (types.index(row["type"]), row["deadline_date"])
    )

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":moneybag: *Funding update* :moneybag:",
            },
        },
    ]

    if calls_recently_added:  # pragma: no branch
        blocks.extend(
            [
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Recently added calls*"},
                },
            ]
        )

        for call in calls_recently_added:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": call["line"]},
                }
            )

    if calls_closing_soon:  # pragma: no branch
        blocks.extend(
            [
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Calls closing within 30 days*",
                    },
                },
            ]
        )

        for call in calls_closing_soon:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": call["line"]},
                }
            )

    blocks.extend(
        [
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Further details for all funding opportunities are available on the <https://docs.google.com/spreadsheets/d/18xM7nu1aD9dZe-eJbqrIRxinO5tjSBZv0EpJRlvz_BI/|funding tracker>.",
                },
            },
        ]
    )

    return json.dumps({"blocks": blocks}, indent=2)


def get_data_from_sheet():  # pragma: no cover
    credentials = service_account.Credentials.from_service_account_file(
        settings.GCP_CREDENTIALS_PATH,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = discovery.build("sheets", "v4", credentials=credentials)

    return (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId="18xM7nu1aD9dZe-eJbqrIRxinO5tjSBZv0EpJRlvz_BI",
            range="Calls",
        )
        .execute()
    )["values"]


if __name__ == "__main__":
    print(main())

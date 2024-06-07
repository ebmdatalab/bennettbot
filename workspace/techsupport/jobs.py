import json
from argparse import ArgumentParser
from datetime import date, datetime, timedelta
from os import environ
from pathlib import Path

from apiclient import discovery
from google.oauth2 import service_account


def config_file():
    return Path(environ["WRITEABLE_DIR"]) / "techsupport_ooo.json"


def today():
    return datetime.today().date()


def convert_date(date_string):
    return date.fromisoformat(date_string)


def get_dates_from_config():
    start = None
    end = None
    config = config_file()
    if config.exists():
        config_dict = json.load(config_file().open())
        start = convert_date(config_dict["start"])
        end = convert_date(config_dict["end"])
    return start, end


def out_of_office_on(start_date, end_date):
    # convert dates to ensure they're valid
    start = convert_date(start_date)
    end = convert_date(end_date)
    config = {"start": start_date, "end": end_date}

    # make sure the dates make sense
    if start > end:
        return "Error: start date must be before end date"
    elif end < today():
        return "Error: Can't set out of office in the past"

    with config_file().open("w") as outfile:
        json.dump(config, outfile)
    if start <= today():
        return f"Tech support out of office now ON until {end_date}"
    return f"Tech support out of office scheduled from {start_date} until {end_date}"


def out_of_office_off():
    config = config_file()
    start, _ = get_dates_from_config()
    config.unlink(missing_ok=True)
    if start and start > today():
        return "Scheduled tech support out of office cancelled"
    return "Tech support out of office OFF"


def out_of_office_status():
    start, end = get_dates_from_config()
    if start is None and end is None:
        return "Tech support out of office is currently OFF."

    if today() > end:
        # OOO was previously set, but dates have expired
        return "Tech support out of office is currently OFF."
    elif today() < start:
        # OOO is set but hasn't started yet
        return (
            f"Tech support out of office is currently OFF.\n"
            f"Scheduled out of office is from {start} until {end}."
        )
    else:
        # OOO is on
        assert start <= today() <= end
        return f"Tech support out of office is currently ON until {end}."


def report_rota():
    rows = get_rota_data_from_sheet()
    rota = {row[0]: (row[1], row[2]) for row in rows[1:] if len(row) >= 3}

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Tech support rota",
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
                        "text": f"Primary tech support this week: {primary} (secondary: {secondary})",
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
        primary, secondary = rota[str(next_monday)]
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Primary tech support next week: {primary} (secondary: {secondary})",
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
            spreadsheetId="1q6EzPQ9iG9Rb-VoYvylObhsJBckXuQdt3Y_pOGysxG8",
            range="Rota",
        )
        .execute()
    )["values"]


if __name__ == "__main__":
    parser = ArgumentParser()

    subparsers = parser.add_subparsers(dest="subparser_name")
    on_parser = subparsers.add_parser("on")
    on_parser.add_argument("start_date")
    on_parser.add_argument("end_date")
    on_parser.set_defaults(function=out_of_office_on)

    off_parser = subparsers.add_parser("off")
    off_parser.set_defaults(function=out_of_office_off)

    status_parser = subparsers.add_parser("status")
    status_parser.set_defaults(function=out_of_office_status)

    rota_parser = subparsers.add_parser("rota")
    rota_parser.set_defaults(function=report_rota)

    args = parser.parse_args()
    if args.subparser_name == "on":
        print(args.function(args.start_date, args.end_date))
    else:
        print(args.function())

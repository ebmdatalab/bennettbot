import argparse
import json
from datetime import date, datetime, timedelta

from workspace.utils import blocks


pairs = {
    "monday": ["Mike", "Jon"],
    "wednesday": ["Mary", "Steve"],
    "friday": ["Thomas", "Katie"],
}


def get_weekday_date(day_of_week):
    weekday = 0  # default to Monday
    if day_of_week == "wednesday":
        weekday = 2
    elif day_of_week == "friday":
        weekday = 4

    offset_days = (weekday - date.weekday(datetime.today())) % 7
    rota_date = datetime.today() + timedelta(offset_days)
    return rota_date.date()


def is_even_week(rota_date):
    week_num = rota_date.isocalendar()[1]
    return week_num % 2


def weekly_rota(args):
    today = date.today()
    primary = is_even_week(today)
    secondary = 0 if primary else 1
    header = "Team Rex stand ups this week"
    days = "\n".join(
        [
            f"Monday: {pairs['monday'][primary]} (backup: {pairs['monday'][secondary]})",
            f"Wednesday: {pairs['wednesday'][primary]} (backup: {pairs['wednesday'][secondary]})",
            f"Friday: {pairs['friday'][primary]} (backup: {pairs['friday'][secondary]})",
        ]
    )

    return json.dumps(blocks.get_basic_header_and_text_blocks(header, days))


def daily_rota(args):
    day_of_week = args.day_of_week
    rota_date = get_weekday_date(day_of_week)

    primary = is_even_week(rota_date)
    secondary = 0 if primary else 1
    header = "Team Rex stand up"
    body = f"{day_of_week.title()}: {pairs[day_of_week][primary]} (backup: {pairs[day_of_week][secondary]})"

    return json.dumps(blocks.get_basic_header_and_text_blocks(header, body))


def get_command_line_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    weekly_parser = subparsers.add_parser("weekly")
    weekly_parser.set_defaults(func=weekly_rota)

    daily_parser = subparsers.add_parser("daily")
    daily_parser.add_argument("day_of_week", choices=("monday", "wednesday", "friday"))
    daily_parser.set_defaults(func=daily_rota)

    return parser


if __name__ == "__main__":
    try:
        args = get_command_line_parser().parse_args()
        print(args.func(args))
    except Exception as e:
        print(
            json.dumps(
                blocks.get_basic_header_and_text_blocks(
                    header_text="An error occurred", texts=str(e)
                )
            )
        )

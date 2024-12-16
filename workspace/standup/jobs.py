import json
from datetime import date, datetime, timedelta

from workspace.utils import blocks


pairs = {
    "monday": ["Mike", "Jon"],
    "wednesday": ["Mary", "Steve"],
    "friday": ["Thomas", "Katie"],
}


def get_weekday_date(day_of_week):
    if day_of_week == "monday":
        weekday = 0
    elif day_of_week == "wednesday":
        weekday = 2
    elif day_of_week == "friday":
        weekday = 4

    offset_days = (weekday - date.weekday(datetime.today())) % 7
    rota_date = datetime.today() + timedelta(offset_days)
    return rota_date.date()


def is_even_week(rota_date):
    week_num = rota_date.isocalendar()[1]
    return week_num % 2


def weekly_rota():
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


def daily_rota(day_of_week):
    rota_date = get_weekday_date(day_of_week)

    primary = is_even_week(rota_date)
    secondary = 0 if primary else 1
    header = "Team Rex stand up"
    body = f"{day_of_week.title()}: {pairs[day_of_week][primary]} (backup: {pairs[day_of_week][secondary]})"

    return json.dumps(blocks.get_basic_header_and_text_blocks(header, body))


if __name__ == "__main__":
    try:
        print(weekly_rota())
    except Exception as e:
        print(
            json.dumps(
                blocks.get_basic_header_and_text_blocks(
                    header_text="An error occurred", texts=str(e)
                )
            )
        )

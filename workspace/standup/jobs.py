import json
from datetime import date

from workspace.utils import blocks


pairs = {
    "Monday": ["Mike", "Jon"],
    "Wednesday": ["Mary", "Steve"],
    "Friday": ["Thomas", "Katie"],
}


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
            f"Monday: {pairs['Monday'][primary]} (backup: {pairs['Monday'][secondary]})",
            f"Wednesday: {pairs['Wednesday'][primary]} (backup: {pairs['Wednesday'][secondary]})",
            f"Friday: {pairs['Friday'][primary]} (backup: {pairs['Friday'][secondary]})",
        ]
    )

    return json.dumps(blocks.get_basic_header_and_text_blocks(header, days))


if __name__ == "__main__":
    print(weekly_rota())

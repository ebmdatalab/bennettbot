import json
from datetime import date, datetime
from pathlib import Path


def config_file():
    return Path(__file__).parent / "ooo.json"


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

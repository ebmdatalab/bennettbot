import abc
import json
from datetime import date, timedelta

from workspace.utils.blocks import get_basic_header_and_text_blocks
from workspace.utils.spreadsheets import get_data_from_sheet


class SpreadsheetRotaReporter(abc.ABC):
    def __init__(self, title: str, spreadsheet_id: str, sheet_range: str):
        self.title = title
        self.spreadsheet_id = spreadsheet_id
        self.sheet_range = sheet_range

    def get_rota_data_from_sheet(self):  # pragma: no cover
        return get_data_from_sheet(self.spreadsheet_id, self.sheet_range)

    def report(self):
        rota = self.get_rota()

        today = date.today()
        this_monday = today - timedelta(days=today.weekday())
        next_monday = this_monday + timedelta(days=7)

        blocks = get_basic_header_and_text_blocks(
            header_text=self.title,
            texts=[
                self.get_rota_text_for_week(rota, this_monday, this_or_next="this"),
                self.get_rota_text_for_week(rota, next_monday, this_or_next="next"),
                self.get_text_linking_rota_spreadsheet(),
            ],
        )
        return json.dumps(blocks, indent=2)

    def get_rota(self):
        rows = self.get_rota_data_from_sheet()
        rota = self.convert_rota_data_to_dictionary(rows)
        return rota

    @abc.abstractmethod
    def convert_rota_data_to_dictionary(self) -> dict:
        """
        Takes the rows returned from get_rota_data_from_sheet and converts them into a dictionary with dates as keys
        """

    @abc.abstractmethod
    def get_rota_text_for_week(self, rota: dict, monday: date, this_or_next: str):
        """
        Returns plain text reporting either the rota or a message saying no rota data was found
        """

    def get_text_linking_rota_spreadsheet(self):
        return f"<https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}|Open rota spreadsheet>"

    @staticmethod
    def format_week(monday: date):
        friday = monday + timedelta(days=4)  # Work week
        return f"{monday.strftime("%d %b")}-{friday.strftime("%d %b")}"

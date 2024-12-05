from datetime import date

from workspace.utils.people import get_slack_username
from workspace.utils.rota import RotaReporter


class DependabotRotaReporter(RotaReporter):
    def convert_rota_data_to_dictionary(self, rows) -> dict:
        return {row[0]: row[1] for row in rows[1:]}

    def get_rota_text_for_week(self, rota: dict, monday: date, this_or_next: str):
        try:
            checker = rota[str(monday)]
            if this_or_next == "this":
                checker = get_slack_username(checker)
            return f"To review dependabot PRs {this_or_next} week ({self.format_week(monday)}): {checker}"
        except KeyError:
            return f"No rota data found for {this_or_next} week"


def report_rota():
    return DependabotRotaReporter(
        title="Dependabot rota",
        spreadsheet_id="1mxAks8tfVEBTSarKoNREsdztW3bTqvIPgV-83GY6CFU",
        sheet_range="Rota",
    ).report()


if __name__ == "__main__":
    print(report_rota())

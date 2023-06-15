import csv
import json
from unittest.mock import patch

from workspace.funding import funding_report


@patch("workspace.funding.funding_report.get_data_from_sheet")
def test_funding_report(get_data_from_sheet, freezer):
    freezer.move_to("2023-06-15")
    with open("tests/workspace/funding-calls.csv") as f:
        get_data_from_sheet.return_value = list(csv.reader(f))
    blocks = json.loads(funding_report.main())
    assert [block["type"] for block in blocks] == [
        "header",
        "divider",
        # Recently added
        "section",
        "section",
        "divider",
        # Closing soon
        "section",
        "section",
        "divider",
        # Further details...
        "section",
    ]
    assert "Research for Social Care" in blocks[3]["text"]["text"]
    assert "Research for Social Care" in blocks[6]["text"]["text"]

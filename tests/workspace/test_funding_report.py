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
        # 2 items
        "section",
        "section",
        "divider",
        # Closing soon
        "section",
        # 2 items
        "section",
        "section",
        "divider",
        # Further details...
        "section",
    ]
    assert "Research for Social Care" in blocks[3]["text"]["text"]
    assert "Research for Social Care1" in blocks[4]["text"]["text"]
    assert "Research for Social Care" in blocks[7]["text"]["text"]
    assert "Research for Social Care1" in blocks[8]["text"]["text"]
    # test that the bad date format in the second item is handled
    assert "closing unknown date: 21Jun 2023 (0 days)" in blocks[8]["text"]["text"]

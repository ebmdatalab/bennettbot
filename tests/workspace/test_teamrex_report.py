from workspace.teamrex import report


def test_report_returns_generated_report(monkeypatch):
    def mock_report(project_num, statuses):
        return "test data"

    monkeypatch.setattr(report.generate_report, "main", mock_report)

    result = report.report()

    assert result == "test data"

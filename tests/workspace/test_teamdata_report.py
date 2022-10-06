from workspace.teamdata import project_report


def test_report_returns_generated_report(monkeypatch):
    def mock_report(project_num, statuses):
        return "test data"

    monkeypatch.setattr(project_report.generate_report, "main", mock_report)

    result = project_report.report()

    assert result == "test data"

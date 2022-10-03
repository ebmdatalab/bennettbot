from workspace.teampipeline import pipeline


def test_report_returns_generated_report(monkeypatch):
    def mock_report(project_num, statuses):
        return "test data"

    monkeypatch.setattr(pipeline.generate_report, "main", mock_report)

    result = pipeline.report()

    assert result == "test data"

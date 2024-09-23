import json
from pathlib import Path
from unittest.mock import patch

import httpretty
import pytest

from workspace.workflows import jobs


WORKFLOWS_MAIN = {
    82728346: "CI",
    88048829: "CodeQL",
    94331150: "Trigger a deploy of opensafely documentation site",
    108457763: "Dependabot Updates",
    113602598: "Local job-server setup CI",
}
WORKFLOWS = {
    **WORKFLOWS_MAIN,
    **{94122733: "Docs"},
}


@pytest.fixture
def mock_airlock_reporter():
    httpretty.enable(allow_net_connect=False)
    httpretty.register_uri(
        httpretty.GET,
        uri="https://api.github.com/repos/opensafely-core/airlock/actions/workflows?format=json",
        match_querystring=True,
        body=Path("tests/workspace/workflows.json").read_text(),
    )
    reporter = jobs.WorkflowReporter("opensafely-core", "airlock")
    httpretty.disable()
    httpretty.reset()
    return reporter


@pytest.mark.parametrize("org", ["opensafely-core", "osc"])
@patch("workspace.workflows.jobs._get_command_line_args")
def test_org_as_target(args, org):
    args.return_value = {"target": org}
    parsed = jobs.parse_args()
    assert parsed == {"org": "opensafely-core", "repo": None}


@pytest.mark.parametrize("org", ["opensafely-core", "osc"])
@patch("workspace.workflows.jobs._get_command_line_args")
def test_repo_as_target(args, org):
    args.return_value = {"target": f"{org}/airlock"}
    parsed = jobs.parse_args()
    assert parsed == {"org": "opensafely-core", "repo": "airlock"}


@patch("workspace.workflows.jobs._get_command_line_args")
def test_invalid_target(args):
    args.return_value = {"target": "some/invalid/input"}
    with pytest.raises(ValueError):
        jobs.parse_args()


@httpretty.activate(allow_net_connect=False)
@pytest.mark.parametrize(
    "branch, num_workflows, workflows",
    [("main", 5, WORKFLOWS_MAIN), (None, 6, WORKFLOWS)],
)
def test_get_workflows(branch, num_workflows, workflows):
    httpretty.register_uri(
        httpretty.GET,
        uri="https://api.github.com/repos/opensafely-core/airlock/actions/workflows?format=json",
        match_querystring=True,
        body=Path("tests/workspace/workflows.json").read_text(),
    )
    reporter = jobs.WorkflowReporter("opensafely-core", "airlock", branch=branch)
    assert len(reporter.workflows) == num_workflows
    assert reporter.workflows == workflows


@httpretty.activate(allow_net_connect=False)
@pytest.mark.parametrize(
    "branch, uri_param",
    [("main", "branch=main&"), (None, "")],
)
def test_get_all_runs(mock_airlock_reporter, branch, uri_param):
    mock_airlock_reporter.branch = branch  # Overwrite branch to test branch=None
    httpretty.register_uri(
        httpretty.GET,
        f"https://api.github.com/repos/opensafely-core/airlock/actions/runs?{uri_param}format=json",
        body=Path("tests/workspace/runs.json").read_text(),
        match_querystring=True,
    )
    all_runs = mock_airlock_reporter.get_all_runs()
    assert len(all_runs) == 6


@patch("workspace.workflows.jobs.WorkflowReporter.get_all_runs")
def test_get_latest_conclusions(mock_all_runs, mock_airlock_reporter):
    all_runs_json = json.loads(Path("tests/workspace/runs.json").read_text())
    mock_all_runs.return_value = all_runs_json["workflow_runs"]

    conclusions = mock_airlock_reporter.get_latest_conclusions()
    assert conclusions == {key: "success" for key in WORKFLOWS_MAIN.keys()}


@pytest.mark.parametrize(
    "run, conclusion",
    [
        ({"status": "completed", "conclusion": "success"}, "success"),
        ({"status": "in_progress", "conclusion": None}, "running"),
        ({"status": "completed", "conclusion": "failure"}, "failure"),
        ({"status": "completed", "conclusion": "skipped"}, "skipped"),
        ({"status": None, "conclusion": None}, "None"),
    ],
)
def test_get_conclusion_for_run(run, conclusion):
    assert jobs.WorkflowReporter.get_conclusion_for_run(run) == conclusion


@pytest.mark.parametrize(
    "conclusion, emoji",
    [
        ("success", ":large_green_circle:"),
        ("running", ":large_yellow_circle:"),
        ("failure", ":red_circle:"),
        ("skipped", ":white_circle:"),
        ("None", ":grey_question:"),
        ("", ":grey_question:"),
    ],
)
@patch("workspace.workflows.jobs.WorkflowReporter.get_latest_conclusions")
def test_summarize_repo(mock_conclusions, mock_airlock_reporter, conclusion, emoji):
    mock_conclusions.return_value = {
        key: conclusion for key in sorted(list(WORKFLOWS_MAIN.keys()))
    }

    blocks = json.loads(mock_airlock_reporter.report(detailed=False))
    assert blocks == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"opensafely-core/airlock: {emoji}{emoji}{emoji}{emoji}{emoji} (<https://github.com/opensafely-core/airlock/actions?query=branch%3Amain|link>)",
            },
        }
    ]


@pytest.mark.parametrize(
    "conclusion, reported, emoji",
    [
        ("success", "Success", ":large_green_circle:"),
        ("running", "Running", ":large_yellow_circle:"),
        ("failure", "Failure", ":red_circle:"),
        ("skipped", "Skipped", ":white_circle:"),
        ("startup_failure", "Startup Failure", ":grey_question:"),
        ("None", "None", ":grey_question:"),
        ("", "", ":grey_question:"),
    ],
)
@patch("workspace.workflows.jobs.WorkflowReporter.get_latest_conclusions")
def test_repo_detailed(
    mock_conclusions, mock_airlock_reporter, conclusion, reported, emoji
):
    mock_conclusions.return_value = {
        key: conclusion for key in sorted(list(WORKFLOWS_MAIN.keys()))
    }
    status = f"{emoji} {reported}"
    blocks = json.loads(mock_airlock_reporter.report(detailed=True))
    assert blocks == [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Workflows for opensafely-core/airlock",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"CI: {status}\nCodeQL: {status}\nTrigger a deploy of opensafely documentation site: {status}\nDependabot Updates: {status}\nLocal job-server setup CI: {status}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://github.com/opensafely-core/airlock/actions?query=branch%3Amain|View Github Actions>",
            },
        },
    ]


@pytest.mark.parametrize(
    "repo, blocks_starting_ind",
    [
        ("airlock", 2),
        (None, 0),
    ],
)
@patch("workspace.workflows.jobs.WorkflowReporter.get_latest_conclusions")
@patch("workspace.workflows.jobs.WorkflowReporter.get_workflows")
@patch("workspace.workflows.jobs.load_config")
def test_valid_org(
    mock_config, mock_workflows, mock_conclusions, repo, blocks_starting_ind
):
    mock_config.return_value = {"repos": {"opensafely-core": ["airlock"]}}
    mock_workflows.return_value = WORKFLOWS_MAIN
    conclusion = "success"
    emoji = ":large_green_circle:"
    mock_conclusions.return_value = {key: conclusion for key in WORKFLOWS_MAIN.keys()}
    blocks = json.loads(
        jobs.main("opensafely-core", repo, detailed=False, branch="main")
    )
    assert (
        blocks
        == [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Workflows for opensafely-core",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":large_green_circle:=Success / :large_yellow_circle:=Running / :red_circle:=Failure / :white_circle:=Skipped / :grey_question:=Other",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"opensafely-core/airlock: {emoji}{emoji}{emoji}{emoji}{emoji} (<https://github.com/opensafely-core/airlock/actions?query=branch%3Amain|link>)",
                },
            },
        ][blocks_starting_ind:]
    )


def test_invalid_org():
    blocks = json.loads(jobs.summarize_org("invalid-org", branch="main"))
    assert blocks == [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "No repos specified for invalid-org",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Use one of the following commands to report a specific repo (provided in the form of `org/repo`):",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "```workflows show [repo]```",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "```workflows show-actions [repo]```",
            },
        },
    ]

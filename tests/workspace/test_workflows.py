import json
from pathlib import Path
from unittest.mock import patch

import httpretty
import pytest

from workspace.workflows import jobs


WORKFLOWS = {
    82728346: "CI",
    88048829: "CodeQL",
    94122733: "Docs",
    94331150: "Trigger a deploy of opensafely documentation site",
    108457763: "Dependabot Updates",
    113602598: "Local job-server setup CI",
}
WORKFLOW_IDS_ON_MAIN = set(WORKFLOWS.keys()).difference({94122733})


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


@patch("workspace.workflows.jobs._get_command_line_args")
def test_org_as_target(args):
    args.return_value = {"target": "opensafely-core"}
    parsed = jobs.parse_args()
    assert parsed == {"org": "opensafely-core", "repo": None}


@patch("workspace.workflows.jobs._get_command_line_args")
def test_repo_as_target(args):
    args.return_value = {"target": "opensafely-core/airlock"}
    parsed = jobs.parse_args()
    assert parsed == {"org": "opensafely-core", "repo": "airlock"}


@patch("workspace.workflows.jobs._get_command_line_args")
def test_invalid_target(args):
    args.return_value = {"target": "some/invalid/input"}
    with pytest.raises(ValueError):
        jobs.parse_args()


def test_get_workflows(mock_airlock_reporter):
    assert mock_airlock_reporter.workflows == WORKFLOWS


@pytest.mark.parametrize(
    "branch, uri_param",
    [("main", "branch=main&"), (None, "")],
)
@httpretty.activate(allow_net_connect=False)
def test_get_all_runs(mock_airlock_reporter, branch, uri_param):
    httpretty.register_uri(
        httpretty.GET,
        f"https://api.github.com/repos/opensafely-core/airlock/actions/runs?{uri_param}format=json",
        body=Path("tests/workspace/runs.json").read_text(),
        match_querystring=True,
    )
    all_runs = mock_airlock_reporter.get_all_runs(branch=branch)
    assert len(all_runs) == 6


@patch("workspace.workflows.jobs.WorkflowReporter.get_all_runs")
def test_get_latest_conclusions(mock_all_runs, mock_airlock_reporter):
    all_runs_json = json.loads(Path("tests/workspace/runs.json").read_text())
    mock_all_runs.return_value = all_runs_json["workflow_runs"]

    conclusions = mock_airlock_reporter.get_latest_conclusions(branch=None)
    assert conclusions == {key: "success" for key in WORKFLOW_IDS_ON_MAIN}


@pytest.mark.parametrize(
    "conclusion, emoji",
    [
        ("success", ":large_green_circle:"),
        ("failure", ":red_circle:"),
        ("skipped", ":white_circle:"),
        (None, ":grey_question:"),
    ],
)
@patch("workspace.workflows.jobs.WorkflowReporter.get_latest_conclusions")
def test_summarize_repo(mock_conclusions, mock_airlock_reporter, conclusion, emoji):
    mock_conclusions.return_value = {
        key: conclusion for key in sorted(list(WORKFLOW_IDS_ON_MAIN))
    }

    blocks = json.loads(mock_airlock_reporter.report(detailed=False, branch=None))
    assert blocks == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely-core/airlock/actions|opensafely-core/airlock>: {emoji}{emoji}{emoji}{emoji}{emoji}",
            },
        }
    ]


@pytest.mark.parametrize(
    "conclusion, reported, emoji",
    [
        ("success", "Success", ":large_green_circle:"),
        ("failure", "Failure", ":red_circle:"),
        ("skipped", "Skipped", ":white_circle:"),
        (None, "None", ":grey_question:"),
    ],
)
@patch("workspace.workflows.jobs.WorkflowReporter.get_latest_conclusions")
def test_repo_detailed(
    mock_conclusions, mock_airlock_reporter, conclusion, reported, emoji
):
    mock_conclusions.return_value = {
        key: conclusion for key in sorted(list(WORKFLOW_IDS_ON_MAIN))
    }
    status = f"{reported} {emoji}"
    blocks = json.loads(mock_airlock_reporter.report(detailed=True, branch=None))
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
                "text": "<https://github.com/opensafely-core/airlock/actions|View Github Actions>",
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
    mock_workflows.return_value = WORKFLOWS
    conclusion = "success"
    emoji = ":large_green_circle:"
    mock_conclusions.return_value = {key: conclusion for key in WORKFLOW_IDS_ON_MAIN}
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
                    "text": ":large_green_circle:=Success / :red_circle:=Failure / :white_circle:=Skipped / :grey_question:=Other",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<https://github.com/opensafely-core/airlock/actions|opensafely-core/airlock>: {emoji}{emoji}{emoji}{emoji}{emoji}",
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

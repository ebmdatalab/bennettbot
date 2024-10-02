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
    94122733: "Docs",
}

CACHE = {
    "opensafely-core/airlock": {
        "timestamp": "2023-09-30T09:00:08Z",
        "conclusions": {str(key): "success" for key in WORKFLOWS_MAIN.keys()},
    }
}


@pytest.fixture
def cache_path(tmp_path):
    yield tmp_path / "test_cache.json"


@pytest.fixture
def mock_airlock_reporter():
    httpretty.enable(allow_net_connect=False)
    # Workflow IDs and names
    httpretty.register_uri(
        httpretty.GET,
        uri="https://api.github.com/repos/opensafely-core/airlock/actions/workflows?format=json",
        match_querystring=True,
        body=Path("tests/workspace/workflows.json").read_text(),
    )
    # Workflow runs
    httpretty.register_uri(
        httpretty.GET,
        "https://api.github.com/repos/opensafely-core/airlock/actions/runs?per_page=100&format=json",
        body=Path("tests/workspace/runs.json").read_text(),
        match_querystring=False,  # Test the querystring separately
    )
    reporter = jobs.RepoWorkflowReporter("opensafely-core/airlock")
    reporter.cache = {}  # Drop the cache and test _load_cache_for_repo separately
    yield reporter
    httpretty.disable()
    httpretty.reset()


@patch("workspace.workflows.jobs._get_command_line_args")
def test_parse_key_argument(args):
    args.return_value = {"key": True}
    assert jobs.parse_args() is None


def test_print_key():
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Workflow status emoji key",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":large_green_circle:=Success",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":large_yellow_circle:=Running",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":red_circle:=Failure",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":white_circle:=Skipped",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":heavy_multiplication_x:=Cancelled",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":ghost:=Missing",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":grey_question:=Other",
            },
        },
    ]
    assert json.loads(jobs.get_text_blocks_for_key()) == blocks


@patch("workspace.workflows.jobs._get_command_line_args")
def test_no_target(args):
    args.return_value = {"key": False}
    with pytest.raises(ValueError):
        jobs.parse_args()


@pytest.mark.parametrize("org", ["opensafely-core", "osc"])
@patch("workspace.workflows.jobs._get_command_line_args")
def test_org_as_target(args, org):
    args.return_value = {"target": org, "key": False}
    parsed = jobs.parse_args()
    assert parsed == {"org": "opensafely-core", "repo": None}


@pytest.mark.parametrize("org", ["opensafely-core", "osc"])
@patch("workspace.workflows.jobs._get_command_line_args")
def test_repo_as_target(args, org):
    args.return_value = {"target": f"{org}/airlock", "key": False}
    parsed = jobs.parse_args()
    assert parsed == {"org": "opensafely-core", "repo": "airlock"}


@patch("workspace.workflows.jobs._get_command_line_args")
def test_invalid_target(args):
    args.return_value = {"target": "some/invalid/input", "key": False}
    with pytest.raises(ValueError):
        jobs.parse_args()


@httpretty.activate(allow_net_connect=False)
def test_get_workflows():
    # get_workflows is called in __init__, so create the instance here
    httpretty.register_uri(
        httpretty.GET,
        uri="https://api.github.com/repos/opensafely-core/airlock/actions/workflows?format=json",
        match_querystring=True,
        body=Path("tests/workspace/workflows.json").read_text(),
    )
    reporter = jobs.RepoWorkflowReporter("opensafely-core/airlock")
    assert len(reporter.workflows) == 5
    assert reporter.workflows == WORKFLOWS_MAIN


def test_cache_file_does_not_exist(mock_airlock_reporter, cache_path):
    assert not cache_path.exists()
    with patch("workspace.workflows.jobs.CACHE_PATH", cache_path):
        assert jobs.load_cache() == {}
        assert mock_airlock_reporter._load_cache_for_repo() == {}


def test_repo_not_cached(mock_airlock_reporter, cache_path):
    # The cache file exists but there is no record for this repo
    mock_cache = {"another/repo": CACHE["opensafely-core/airlock"]}
    with open(cache_path, "w") as f:
        json.dump(mock_cache, f)
    with patch("workspace.workflows.jobs.CACHE_PATH", cache_path):
        assert mock_airlock_reporter._load_cache_for_repo() == {}


def test_get_runs_since_last_retrieval(mock_airlock_reporter, cache_path):
    # Create the cache and test that it is loaded
    with open(cache_path, "w") as f:
        json.dump(CACHE, f)
    with patch("workspace.workflows.jobs.CACHE_PATH", cache_path):
        mock_airlock_reporter.cache = mock_airlock_reporter._load_cache_for_repo()
    assert mock_airlock_reporter.cache == CACHE["opensafely-core/airlock"]

    mock_airlock_reporter.get_runs_since_last_retrieval()
    assert httpretty.last_request().querystring == {
        "branch": ["main"],
        "per_page": ["100"],
        "format": ["json"],
        "created": [">=2023-09-30T09:00:08Z"],
    }


def test_all_workflows_found(mock_airlock_reporter, cache_path):
    with patch("workspace.workflows.jobs.CACHE_PATH", cache_path):
        conclusions = mock_airlock_reporter.get_latest_conclusions()
    assert conclusions == {key: "success" for key in WORKFLOWS_MAIN.keys()}


def test_some_workflows_not_found(mock_airlock_reporter, cache_path):
    mock_airlock_reporter.workflows[1234] = "Workflow that only exists in the cache"
    mock_airlock_reporter.cache = {
        "timestamp": None,
        "conclusions": {"1234": "running"},
    }

    mock_airlock_reporter.workflows[5678] = "Workflow that will not be found"
    mock_airlock_reporter.workflow_ids = set(mock_airlock_reporter.workflows.keys())
    with patch("workspace.workflows.jobs.CACHE_PATH", cache_path):
        conclusions = mock_airlock_reporter.get_latest_conclusions()
    assert len(mock_airlock_reporter.workflow_ids) == 7
    assert conclusions == {
        **{key: "success" for key in WORKFLOWS_MAIN.keys()},
        1234: "running",
        5678: "missing",
    }


@patch("workspace.workflows.jobs.RepoWorkflowReporter.write_cache_to_file")
def test_cache_creation(mock_write, mock_airlock_reporter, freezer):
    mock_write.return_value = None  # Disable writing to file and test separately
    assert mock_airlock_reporter.cache == {}
    freezer.move_to("2023-09-30 09:00:08")
    _ = mock_airlock_reporter.get_latest_conclusions()
    assert mock_airlock_reporter.cache == CACHE["opensafely-core/airlock"]


def test_write_to_cache_file(mock_airlock_reporter, cache_path):
    mock_airlock_reporter.cache = CACHE["opensafely-core/airlock"]
    with patch("workspace.workflows.jobs.CACHE_PATH", cache_path):
        mock_airlock_reporter.write_cache_to_file()
    assert json.loads(cache_path.read_text()) == CACHE


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
    assert jobs.RepoWorkflowReporter.get_conclusion_for_run(run) == conclusion


@pytest.mark.parametrize(
    "conclusion, emoji",
    [
        ("success", ":large_green_circle:"),
        ("None", ":grey_question:"),
        ("", ":grey_question:"),
    ],
)
def test_get_summary_block(conclusion, emoji):
    conclusions = [conclusion for _ in range(5)]
    block = jobs.get_summary_block("opensafely-core/airlock", conclusions)
    assert block == {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"<https://github.com/opensafely-core/airlock/actions?query=branch%3Amain|opensafely-core/airlock>: {emoji*5}",
        },
    }


@httpretty.activate(allow_net_connect=False)
@pytest.mark.parametrize(
    "conclusion, reported, emoji",
    [
        ("success", "Success", ":large_green_circle:"),
        ("startup_failure", "Startup Failure", ":grey_question:"),  # Handle underscore
        ("None", "None", ":grey_question:"),
        ("", "", ":grey_question:"),
    ],
)
@patch("workspace.workflows.jobs.RepoWorkflowReporter.get_latest_conclusions")
def test_main_for_repo(mock_conclusions, conclusion, reported, emoji):
    # Call main with a valid org name and a valid repo name
    # No need to mock CACHE_PATH since get_latest_conclusions is mocked
    httpretty.register_uri(
        httpretty.GET,
        uri="https://api.github.com/repos/opensafely-core/airlock/actions/workflows?format=json",
        match_querystring=True,
        body=Path("tests/workspace/workflows.json").read_text(),
    )
    mock_conclusions.return_value = {
        key: conclusion for key in sorted(list(WORKFLOWS_MAIN.keys()))
    }
    status = f"{emoji} {reported}"
    blocks = json.loads(jobs.main("opensafely-core", "airlock"))
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


@patch("workspace.workflows.jobs.RepoWorkflowReporter.get_runs_since_last_retrieval")
@patch("workspace.workflows.jobs.RepoWorkflowReporter.get_workflows")
@patch(
    "workspace.workflows.config.REPOS", {"opensafely-core": ["airlock", "failing-repo"]}
)
def test_main_for_organisation(mock_workflows, mock_runs, cache_path):
    # Call main with a valid org and repo=None

    # Mocks
    mock_workflows.return_value = WORKFLOWS_MAIN
    mock_runs.return_value = []  # Read from the cache
    mock_cache = {
        **CACHE,  # The successful one appears first in the cache
        "opensafely-core/failing-repo": {
            "timestamp": "2023-09-29T19:00:08Z",
            "conclusions": {str(key): "failure" for key in WORKFLOWS_MAIN.keys()},
        },
    }
    with open(cache_path, "w") as f:
        json.dump(mock_cache, f)

    # Test main
    with patch("workspace.workflows.jobs.CACHE_PATH", cache_path):
        blocks = json.loads(jobs.main("opensafely-core", repo=None))
    green = ":large_green_circle:"
    red = ":red_circle:"
    assert blocks == [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Workflows for opensafely-core repos",
            },
        },
        {  # Failing repo should appear first
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely-core/failing-repo/actions?query=branch%3Amain|opensafely-core/failing-repo>: {red*5}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely-core/airlock/actions?query=branch%3Amain|opensafely-core/airlock>: {green*5}",
            },
        },
    ]


@patch("workspace.workflows.jobs.RepoWorkflowReporter.get_latest_conclusions")
@patch("workspace.workflows.jobs.RepoWorkflowReporter.get_workflows")
@patch(
    "workspace.workflows.config.REPOS",
    {
        "opensafely-core": ["airlock"],
        "opensafely": ["documentation"],
    },
)
def test_main_for_all_orgs(mock_workflows, mock_conclusions, cache_path):
    # Call main with org="all" and repo=None
    # Use same workflows and conclusions for convenience
    mock_workflows.return_value = WORKFLOWS_MAIN
    conclusion = "success"
    emoji = ":large_green_circle:"
    mock_conclusions.return_value = {key: conclusion for key in WORKFLOWS_MAIN.keys()}
    with patch("workspace.workflows.jobs.CACHE_PATH", cache_path):
        blocks = json.loads(jobs.main("all", repo=None))
    assert blocks == [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Workflows for key repos",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely-core/airlock/actions?query=branch%3Amain|opensafely-core/airlock>: {emoji*5}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely/documentation/actions?query=branch%3Amain|opensafely/documentation>: {emoji*5}",
            },
        },
    ]


def test_main_for_invalid_org():
    # Call main with an invalid org
    blocks = json.loads(jobs.main("invalid-org", repo=None))
    assert blocks == [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "invalid-org was not recognised",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Run `@test_username workflows help` to see the available organisations.",
            },
        },
    ]

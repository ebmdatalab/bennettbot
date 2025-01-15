import functools
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from mocket import Mocket, Mocketizer, mocketize
from mocket.mockhttp import Entry

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
    # Workflow IDs and names
    Entry.single_register(
        Entry.GET,
        "https://api.github.com/repos/opensafely-core/airlock/actions/workflows?format=json",
        body=Path("tests/workspace/workflows.json").read_text(),
        match_querystring=True,
    )

    # Workflow runs
    Entry.single_register(
        Entry.GET,
        "https://api.github.com/repos/opensafely-core/airlock/actions/runs?per_page=100&format=json",
        body=Path("tests/workspace/runs.json").read_text(),
        match_querystring=False,  # Test the querystring separately
    )
    with Mocketizer(strict_mode=True):
        reporter = jobs.RepoWorkflowReporter("opensafely-core/airlock")
        reporter.cache = {}  # Drop the cache and test _load_cache_for_repo separately
        yield reporter


class MockRepoWorkflowReporter(jobs.RepoWorkflowReporter):
    # A mock class to allow us to vary the conclusions returned by get_latest_conclusions.

    def get_workflows(self) -> dict:
        return WORKFLOWS_MAIN

    def get_runs(self, since_last_retrieval) -> list:
        # Have no new runs so that results are read from a separately patched mock cache
        return []

    def write_cache_to_file(self):
        # Skip writing to the cache file as this is already tested separately
        pass


def use_mock_results(patch_settings):
    def decorator_use_mock_results(func):
        @functools.wraps(func)
        def wrapper_use_mock_results(*args, **kwargs):
            # Mock config
            mock_repos_config = {
                r["repo"]: {"org": r["org"], "team": r["team"]} for r in patch_settings
            }
            # Mock cache
            keys = sorted(list(WORKFLOWS_MAIN.keys()))
            mock_cache = {
                f"{r['org']}/{r['repo']}": {
                    "timestamp": "2023-09-30T09:00:08Z",
                    "conclusions": {
                        str(keys[i]): conc for i, conc in enumerate(r["conclusions"])
                    },
                }
                for r in patch_settings
            }
            # Patch the config and use results from the mock cache
            with (
                patch("workspace.workflows.config.REPOS", mock_repos_config),
                patch("workspace.workflows.jobs.load_cache", return_value=mock_cache),
                patch(
                    "workspace.workflows.jobs.RepoWorkflowReporter",
                    MockRepoWorkflowReporter,
                ),
            ):
                return func(*args, **kwargs)

        return wrapper_use_mock_results

    return decorator_use_mock_results


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
    assert json.loads(jobs.get_text_blocks_for_key(None)) == blocks


@pytest.mark.parametrize("org", ["opensafely-core", "osc"])
def test_org_as_target(org):
    args = jobs.get_command_line_parser().parse_args(f"show --target {org}".split())

    with patch("workspace.workflows.jobs._main") as mock__main:
        jobs.main(args)
        mock__main.assert_called_once_with("opensafely-core", None, False)


@pytest.mark.parametrize("org", ["opensafely-core", "osc"])
def test_org_and_repo_as_target(org):
    args = jobs.get_command_line_parser().parse_args(
        f"show --target {org}/airlock".split()
    )

    with patch("workspace.workflows.jobs._main") as mock__main:
        jobs.main(args)
        mock__main.assert_called_once_with("opensafely-core", "airlock", False)


def test_repo_only_as_target():
    args = jobs.get_command_line_parser().parse_args("show --target airlock".split())

    with patch("workspace.workflows.jobs._main") as mock__main:
        jobs.main(args)
        mock__main.assert_called_once_with("opensafely-core", "airlock", False)


def test_website_repo_as_target():
    args = jobs.get_command_line_parser().parse_args(
        "show --target http://bennett.ox.ac.uk".split()
    )
    with patch("workspace.workflows.jobs._main") as mock__main:
        jobs.main(args)
        mock__main.assert_called_once_with("ebmdatalab", "bennett.ox.ac.uk", False)


def test_invalid_target():
    args = jobs.get_command_line_parser().parse_args(
        "show --target some/invalid/input".split()
    )
    blocks = json.loads(jobs.main(args))
    assert blocks[0] == {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "some/invalid/input was not recognised",
        },
    }


def test_catch_unhandled_error():
    args = jobs.get_command_line_parser().parse_args(
        "show --target some/invalid/input".split()
    )
    with patch(
        "workspace.workflows.jobs.report_invalid_target",
        return_value=None,
        side_effect=Exception("Unknown error"),
    ):
        blocks = json.loads(jobs.main(args))
    assert blocks == [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "An error occurred reporting workflows for some/invalid/input",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Unknown error",
            },
        },
    ]


@mocketize(strict_mode=True)
def test_get_workflows():
    # get_workflows is called in __init__, so create the instance here
    Entry.single_register(
        Entry.GET,
        "https://api.github.com/repos/opensafely-core/airlock/actions/workflows?format=json",
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

    mock_airlock_reporter.get_runs(since_last_retrieval=True)
    assert Mocket.last_request().querystring == {
        "branch": ["main"],
        "per_page": ["100"],
        "format": ["json"],
        "created": [">=2023-09-30T09:00:08Z"],
    }


def test_all_workflows_found(mock_airlock_reporter, cache_path):
    with patch("workspace.workflows.jobs.CACHE_PATH", cache_path):
        conclusions = mock_airlock_reporter.get_latest_conclusions()
    assert conclusions == {key: "success" for key in WORKFLOWS_MAIN.keys()}
    assert "created" not in Mocket.last_request().querystring


def test_some_workflows_not_found(mock_airlock_reporter, cache_path):
    mock_airlock_reporter.workflows[1234] = "Workflow that only exists in the cache"
    mock_airlock_reporter.cache = {
        "timestamp": "2023-09-30T09:00:08Z",
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


@pytest.mark.parametrize(
    "conclusion,created_in_querystring", [("success", True), ("failure", False)]
)
def test_get_runs_beyond_last_retrieval_if_not_all_successful(
    conclusion, created_in_querystring, mock_airlock_reporter, cache_path
):
    mock_airlock_reporter.workflows[1234] = "Some failing workflow"
    mock_airlock_reporter.cache = {
        "timestamp": "2023-09-30T09:00:08Z",
        "conclusions": {"1234": conclusion},
    }
    mock_airlock_reporter.workflow_ids = set(mock_airlock_reporter.workflows.keys())
    with patch("workspace.workflows.jobs.CACHE_PATH", cache_path):
        conclusions = mock_airlock_reporter.get_latest_conclusions()
    assert len(mock_airlock_reporter.workflow_ids) == 6
    assert conclusions == {
        **{key: "success" for key in WORKFLOWS_MAIN.keys()},
        1234: conclusion,
    }

    querystring = Mocket.last_request().querystring
    assert ("created" in querystring) == created_in_querystring


@patch("workspace.workflows.jobs.RepoWorkflowReporter.write_cache_to_file")
def test_cache_creation(mock_write, mock_airlock_reporter, freezer):
    mock_write.return_value = None  # Disable writing to file and test separately
    assert mock_airlock_reporter.cache == {}
    freezer.move_to("2023-09-30 09:00:08")
    mock_airlock_reporter.get_latest_conclusions()
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
    conclusions = [conclusion] * 5
    block = jobs.get_summary_block("opensafely-core/airlock", conclusions)
    assert block == {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"<https://github.com/opensafely-core/airlock/actions?query=branch%3Amain|opensafely-core/airlock>: {emoji * 5}",
        },
    }


@mocketize(strict_mode=True)
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
def test_main_show_repo(mock_conclusions, conclusion, reported, emoji):
    # Call main for a single repo (opensafely-core/airlock)
    # No need to mock CACHE_PATH since get_latest_conclusions is mocked
    Entry.single_register(
        Entry.GET,
        "https://api.github.com/repos/opensafely-core/airlock/actions/workflows?format=json",
        match_querystring=True,
        body=Path("tests/workspace/workflows.json").read_text(),
    )
    mock_conclusions.return_value = {
        key: conclusion for key in sorted(list(WORKFLOWS_MAIN.keys()))
    }
    status = f"{emoji} {reported}"
    args = jobs.get_command_line_parser().parse_args(
        "show --target opensafely-core/airlock".split()
    )
    blocks = json.loads(jobs.main(args))
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


@use_mock_results(
    [
        {
            "org": "opensafely-core",
            "repo": "airlock",
            "team": "Team RAP",
            "conclusions": ["success"] * 5,
        },
        {
            "org": "opensafely-core",
            "repo": "failing-repo",
            "team": "Team REX",
            "conclusions": ["failure"] * 5,
        },
    ]
)
def test_main_show_org():
    # Call main for an organisation without skipping successful workflows
    # The failing repo should appear first
    args = jobs.get_command_line_parser().parse_args("show --target osc".split())

    blocks = json.loads(jobs.main(args))
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
                "text": f"<https://github.com/opensafely-core/failing-repo/actions?query=branch%3Amain|opensafely-core/failing-repo>: {':red_circle:' * 5}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely-core/airlock/actions?query=branch%3Amain|opensafely-core/airlock>: {':large_green_circle:' * 5}",
            },
        },
    ]


@use_mock_results(
    [
        {
            "org": "opensafely-core",
            "repo": "airlock",
            "team": "Team RAP",
            "conclusions": ["success"] * 5,
        },
        {
            "org": "opensafely",
            "repo": "documentation",
            "team": "Team REX",
            "conclusions": ["success"] * 5,
        },
    ]
)
def test_main_show_all():
    # Call main for all repos without skipping successful workflows
    args = jobs.get_command_line_parser().parse_args("show --target all".split())
    blocks = json.loads(jobs.main(args))
    assert blocks == [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Workflows for Team REX",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely/documentation/actions?query=branch%3Amain|opensafely/documentation>: {':large_green_circle:' * 5}",
            },
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Workflows for Team RAP",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely-core/airlock/actions?query=branch%3Amain|opensafely-core/airlock>: {':large_green_circle:' * 5}",
            },
        },
    ]


@patch(
    "workspace.workflows.config.WORKFLOWS_KNOWN_TO_FAIL",
    {
        "opensafely/failing-repo": [82728346, 88048829, 94331150, 108457763, 113602598],
    },
)
@use_mock_results(
    [
        {
            "org": "opensafely-core",
            "repo": "airlock",
            "team": "Team RAP",
            "conclusions": ["success"] * 5,
        },
        {
            "org": "opensafely",
            "repo": "failing-repo",
            "team": "Team REX",
            "conclusions": ["failure"] * 5,
        },
    ]
)
def test_main_show_all_skip_failures():
    # Call main for all repos without skipping successful workflows
    # Since all workflows in failing-repo are known to fail, it should be skipped entirely
    args = jobs.get_command_line_parser().parse_args("show --target all".split())
    blocks = json.loads(jobs.main(args))
    assert blocks == [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Workflows for Team RAP",
            },
        },
        {  # Only the Team RAP section should appear
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely-core/airlock/actions?query=branch%3Amain|opensafely-core/airlock>: {':large_green_circle:' * 5}",
            },
        },
    ]


@use_mock_results(
    [
        {
            "org": "opensafely-core",
            "repo": "airlock",
            "team": "Team RAP",
            "conclusions": ["success"] * 5,
        },
        {
            "org": "opensafely",
            "repo": "documentation",
            "team": "Team REX",
            "conclusions": ["success"] * 5,
        },
    ]
)
def test_main_show_failed_empty():
    # Call main for all repos with skipping successful workflows
    # No failed workflows so state so
    args = jobs.get_command_line_parser().parse_args(
        "show --target all --skip-successful".split()
    )
    blocks = json.loads(jobs.main(args))
    assert blocks == [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "No workflow failures to report!",
            },
        },
    ]


@use_mock_results(
    [
        {
            "org": "opensafely-core",
            "repo": "airlock",
            "team": "Team RAP",
            "conclusions": ["success"] * 5,
        },
        {
            "org": "opensafely",
            "repo": "failing-repo",
            "team": "Team REX",
            "conclusions": ["failure"] * 5,
        },
    ]
)
def test_main_show_failed_found():
    # Call main for all repos with skipping successful workflows
    # Only the failing repo should appear
    args = jobs.get_command_line_parser().parse_args(
        "show --target all --skip-successful".split()
    )

    blocks = json.loads(jobs.main(args))
    assert blocks == [
        {  # Only the Team REX section should appear
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Workflows for Team REX",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely/failing-repo/actions?query=branch%3Amain|opensafely/failing-repo>: {':red_circle:' * 5}",
            },
        },
    ]


@patch(
    "workspace.workflows.config.WORKFLOWS_KNOWN_TO_FAIL",
    {
        # Second-last workflow is known to fail
        "opensafely-core/airlock": [108457763],
        "opensafely/failing-repo": [108457763],
    },
)
@use_mock_results(
    [
        {
            "org": "opensafely-core",
            "repo": "airlock",
            "team": "Team RAP",
            # Known failure fails as expected
            "conclusions": ["success", "success", "success", "failure", "success"],
        },
        {
            "org": "opensafely",
            "repo": "failing-repo",
            "team": "Team REX",
            # Known failure unexpectedly passes
            "conclusions": ["failure", "failure", "failure", "success", "failure"],
        },
    ]
)
def test_main_show_failed_skipped():
    # Call main for all repos with skipping successful workflows
    # Skip failures that are already known
    args = jobs.get_command_line_parser().parse_args(
        "show --target all --skip-successful".split()
    )

    blocks = json.loads(jobs.main(args))
    assert blocks == [
        {  # Only the Team REX section should appear and all workflows should be present
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Workflows for Team REX",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<https://github.com/opensafely/failing-repo/actions?query=branch%3Amain|opensafely/failing-repo>: {':large_green_circle:'}{':red_circle:' * 4}",
            },
        },
    ]


def test_main_show_invalid_target():
    # Call main with an invalid org
    args = jobs.get_command_line_parser().parse_args(
        "show --target invalid-org".split()
    )
    blocks = json.loads(jobs.main(args))
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
                "text": "Argument must be a known organisation or repo, or a repo given as [org/repo].",
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


@patch(
    "workspace.workflows.config.CUSTOM_JOBS",
    {
        "check-links": {
            "header_text": "Link-checking workflows",
            "workflows": {
                "opensafely/documentation": [82728346],
                "ebmdatalab/bennett.ox.ac.uk": [82728346],
                "ebmdatalab/opensafely.org": [82728346],
                "ebmdatalab/team-manual": [82728346],
            },
        }
    },
)
@use_mock_results(
    [
        {
            "org": "opensafely",
            "repo": "documentation",
            "team": "Tech shared",
            "conclusions": ["success"] * 5,
        },
        {
            "org": "ebmdatalab",
            "repo": "team-manual",
            "team": "Tech shared",
            "conclusions": ["failure"] * 5,
        },
        {
            "org": "ebmdatalab",
            "repo": "bennett.ox.ac.uk",
            "team": "Tech shared",
            "conclusions": ["success"] * 5,
        },
        {
            "org": "ebmdatalab",
            "repo": "opensafely.org",
            "team": "Tech shared",
            "conclusions": ["failure"] * 5,
        },
    ]
)
def test_check_links():
    args = jobs.get_command_line_parser().parse_args(
        "custom --job-name check-links".split()
    )
    blocks = json.loads(jobs.get_blocks_for_custom_workflow_list(args))
    assert blocks == [
        {  # Only 1 emoji should appear for each repo
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Link-checking workflows",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://github.com/opensafely/documentation/actions?query=branch%3Amain|opensafely/documentation>: :large_green_circle:",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://github.com/ebmdatalab/bennett.ox.ac.uk/actions?query=branch%3Amain|ebmdatalab/bennett.ox.ac.uk>: :large_green_circle:",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://github.com/ebmdatalab/opensafely.org/actions?query=branch%3Amain|ebmdatalab/opensafely.org>: :red_circle:",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://github.com/ebmdatalab/team-manual/actions?query=branch%3Amain|ebmdatalab/team-manual>: :red_circle:",
            },
        },
    ]

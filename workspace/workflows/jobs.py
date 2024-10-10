import argparse
import json
import os
from datetime import datetime
from urllib.parse import urljoin

import requests

from bennettbot import settings
from workspace.utils.blocks import (
    get_basic_header_and_text_blocks,
    get_header_block,
    get_text_block,
)
from workspace.workflows import config


CACHE_PATH = settings.WRITEABLE_DIR / "workflows_cache.json"
TOKEN = os.environ["DATA_TEAM_GITHUB_API_TOKEN"]  # requires "read:project" and "repo"
EMOJI = {
    "success": ":large_green_circle:",
    "running": ":large_yellow_circle:",
    "failure": ":red_circle:",
    "skipped": ":white_circle:",
    "cancelled": ":heavy_multiplication_x:",
    "missing": ":ghost:",
    "other": ":grey_question:",
}


def get_emoji(conclusion) -> str:
    return EMOJI.get(conclusion, EMOJI["other"])


def get_locations_for_team(team: str) -> list[str]:
    return [
        f'{v["org"]}/{repo}' for repo, v in config.REPOS.items() if v["team"] == team
    ]


def get_locations_for_org(org: str) -> list[str]:
    return [f"{org}/{repo}" for repo, v in config.REPOS.items() if v["org"] == org]


def report_invalid_org(org) -> str:
    blocks = get_basic_header_and_text_blocks(
        header_text=f"{org} was not recognised",
        texts=f"Run `@{settings.SLACK_APP_USERNAME} workflows help` to see the available organisations.",
    )
    return json.dumps(blocks)


def get_api_result_as_json(url: str, params: dict | None = None) -> dict:
    params = params or {}
    params["format"] = "json"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    return json.loads(CACHE_PATH.read_text())


def get_github_actions_link(location):
    return f"https://github.com/{location}/actions?query=branch%3Amain"


class RepoWorkflowReporter:
    def __init__(self, location):
        """
        Retrieves and reports on the status of workflow runs on the main branch in a specified repo.
        Workflows that are not on the main branch are skipped.

        Creating an instance of this class will automatically call the GitHub API to get a list of workflow IDs and their names.
        Subsequently calling get_latest_conclusions() will call a different endpoint of the API to get the status and conclusion for the most recent run of each workflow.
        workflows_cache.json is updated with the conclusions and the timestamp of the retrieval, and API calls are only made for new runs since the last retrieval.

        report() will return a full JSON message with blocks for each workflow where the statuses of workflows are represented by emojis, as defined in the EMOJI dictionary.

        Functions outside of this class are used to generate summary reports from the conclusions returned from get_latest_conclusions() or loaded from the cache file.

        Parameters:
            location: str
                The location of the repo in the format "org/repo" (e.g. "opensafely/documentation")
        """
        self.location = location
        self.base_api_url = f"https://api.github.com/repos/{self.location}/"
        self.github_actions_link = get_github_actions_link(self.location)

        self.workflows = self.get_workflows()  # Dict of workflow_id: workflow_name
        self.workflow_ids = set(self.workflows.keys())

        self.cache = self._load_cache_for_repo()

    def _load_cache_for_repo(self) -> dict:
        return load_cache().get(self.location, {})

    @property
    def last_retrieval_timestamp(self):
        # Do not declare in __init__ to update this when self.cache is updated
        return self.cache.get("timestamp", None)

    def _get_json_response(self, path, params=None):
        url = urljoin(self.base_api_url, path)
        return get_api_result_as_json(url, params)

    def get_workflows(self) -> dict:
        results = self._get_json_response("actions/workflows")["workflows"]
        workflows = {wf["id"]: wf["name"] for wf in results}
        self.remove_workflows_skipped_on_main(workflows)
        return workflows

    def remove_workflows_skipped_on_main(self, workflows):
        skipped = config.SKIPPED_WORKFLOWS_ON_MAIN.get(self.location, [])
        for workflow_id in skipped:
            workflows.pop(workflow_id, None)

    def get_runs_since_last_retrieval(self) -> list:
        params = {"branch": "main", "per_page": 100}
        if self.last_retrieval_timestamp:  # If not present do not pass anything at all
            params["created"] = ">=" + self.last_retrieval_timestamp
        return self._get_json_response("actions/runs", params=params)["workflow_runs"]

    def get_latest_conclusions(self) -> dict:
        """
        Use the GitHub API to get the conclusion of the most recent run for each workflow.
        Update the cache file with the conclusions and the timestamp of the retrieval.
        """
        # Use the moment just before calling the GitHub API as the timestamp
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        new_runs = self.get_runs_since_last_retrieval()
        latest_runs, missing_ids = self.find_latest_for_each_workflow(new_runs)
        conclusions = {
            run["workflow_id"]: self.get_conclusion_for_run(run) for run in latest_runs
        }
        self.fill_in_conclusions_for_missing_ids(conclusions, missing_ids)

        self.cache = {
            "timestamp": timestamp,
            # To be consistent with the JSON file which has the IDs as strings
            "conclusions": {str(k): v for k, v in conclusions.items()},
        }

        pending = "running" in conclusions.values() or "queued" in conclusions.values()
        if not pending:  # Only write cache to file if the status is final
            self.write_cache_to_file()
        return conclusions

    @staticmethod
    def get_conclusion_for_run(run) -> str:
        aliases = {"in_progress": "running"}
        if run["conclusion"] is None:
            status = str(run["status"])
            return aliases.get(status, status)
        return run["conclusion"]

    def fill_in_conclusions_for_missing_ids(self, conclusions, missing_ids):
        """
        For workflows that have not run since the last retrieval, use the conclusion from the cache.
        If no conclusion is found in the cache, mark the workflow as missing.
        """
        previous_conclusions = self.cache.get("conclusions", {})
        for workflow_id in missing_ids:
            id_str = str(workflow_id)  # In the cache JSON, IDs are stored as strings
            conclusions[workflow_id] = previous_conclusions.get(id_str, "missing")
        return

    def write_cache_to_file(self):
        cache_file_contents = load_cache()
        cache_file_contents[self.location] = self.cache
        with open(CACHE_PATH, "w") as f:
            f.write(json.dumps(cache_file_contents))

    def report(self) -> str:
        # This needs to be a class method as it uses self.workflows for names
        def format_text(workflow_id, conclusion) -> str:
            name = self.workflows[workflow_id]
            emoji = get_emoji(conclusion)
            return f"{name}: {emoji} {conclusion.title().replace('_', ' ')}"

        conclusions = self.get_latest_conclusions()
        lines = [format_text(wf, conclusion) for wf, conclusion in conclusions.items()]
        blocks = [
            get_header_block(f"Workflows for {self.location}"),
            get_text_block("\n".join(lines)),  # Show in one block for compactness
            get_text_block(f"<{self.github_actions_link}|View Github Actions>"),
        ]
        return json.dumps(blocks)

    def find_latest_for_each_workflow(self, all_runs) -> list:
        latest_runs = []
        found_ids = set()
        for run in all_runs:
            if run["workflow_id"] in found_ids:
                continue
            latest_runs.append(run)
            found_ids.add(run["workflow_id"])
            if found_ids == self.workflow_ids:
                return latest_runs, set()
        missing_ids = self.workflow_ids - found_ids
        return latest_runs, missing_ids


def get_summary_block(location: str, conclusions: list) -> str:
    link = get_github_actions_link(location)
    emojis = "".join([get_emoji(c) for c in conclusions])
    return get_text_block(f"<{link}|{location}>: {emojis}")


def get_success_rate(conclusions) -> float:
    return conclusions.count("success") / len(conclusions)


def _summarise(header_text: str, locations: list[str], skip_successful: bool) -> list:
    unsorted = {}
    for location in locations:
        wf_conclusions = RepoWorkflowReporter(location).get_latest_conclusions()
        if skip_successful and get_success_rate(list(wf_conclusions.values())) == 1:
            continue
        unsorted[location] = list(wf_conclusions.values())

    key = lambda item: get_success_rate(item[1])
    conclusions = sorted(unsorted.items(), key=key)

    blocks = [
        get_header_block(header_text),
        *[get_summary_block(loc, conc) for loc, conc in conclusions],
    ]
    return blocks


def summarise_team(team: str, skip_successful: bool) -> list:
    header = f"Workflows for {team}"
    locations = get_locations_for_team(team)
    return _summarise(header, locations, skip_successful)


def summarise_all(skip_successful) -> list:
    # Show in sections by team
    blocks = []
    for team in config.TEAMS:
        team_blocks = summarise_team(team, skip_successful)
        if len(team_blocks) > 1:
            blocks.extend(team_blocks)
    return blocks


def summarise_org(org, skip_successful) -> list:
    header_text = f"Workflows for {org} repos"
    locations = get_locations_for_org(org)
    blocks = _summarise(header_text, locations, skip_successful)
    return blocks


def main(args) -> str:
    target = args.target.split("/")
    if len(target) == 2:
        org, repo = target
    elif len(target) == 1:
        if target[0] in config.REPOS.keys():  # Known repo
            org, repo = config.REPOS[target[0]]["org"], target[0]
        else:  # Assume org
            org, repo = target[0], None
    else:  # Invalid target format
        raise ValueError(
            "Argument must be a known organisation or repo, or a repo given as [org/repo]"
        )

    # Org may be a shorthand
    org = config.SHORTHANDS.get(org, org)
    return _main(org, repo, args.skip_successful)


def _main(org, repo, skip_successful=False) -> str:
    """
    Main function to report on the status of workflows in a specified repo or org.
    args:
        org: str
            The organisation or shorthand for the organisation to report on. A special value of "all" will report on all orgs.
        repo: str | None
            The repo to report on. If None, all repos specified by "org" will be reported on.
        skip_successful: bool
            If True, repos with all successful (i.e. all green) workflows will be skipped. Only used for summary functions."""
    if org == "all":
        # Summarise status for all repos in all orgs
        return json.dumps(summarise_all(skip_successful))
    elif org in config.SHORTHANDS.values():  # Valid organisation
        if repo is None:
            # Summarise status for multiple repos in an org
            return json.dumps(summarise_org(org, skip_successful))
        # Single repo usage: Report status for all workflows in a specified repo
        return RepoWorkflowReporter(f"{org}/{repo}").report()
    else:
        return report_invalid_org(org)


def get_text_blocks_for_key(args) -> str:
    blocks = get_basic_header_and_text_blocks(
        header_text="Workflow status emoji key",
        texts=[f"{v}={k.title()}" for k, v in EMOJI.items()],
    )
    return json.dumps(blocks)


def get_command_line_parser():  # pragma: no cover
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(required=True)

    # Main task: show workflows
    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("--target", required=True)
    show_parser.add_argument("--skip-successful", action="store_true", default=False)
    show_parser.set_defaults(func=main)

    # Display key
    key_parser = subparsers.add_parser("key")
    key_parser.set_defaults(func=get_text_blocks_for_key)
    return parser


if __name__ == "__main__":
    args = get_command_line_parser().parse_args()
    print(args.func(args))

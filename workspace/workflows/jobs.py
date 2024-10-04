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


def _summarise(header_text: str, locations: list[str], skip_successful: bool) -> str:
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
    return json.dumps(blocks)


def summarise_all(skip_successful) -> str:
    header_text = "Workflows for key repos"
    locations = [
        f"{org}/{repo}" for org, repos in config.REPOS.items() for repo in repos
    ]
    return _summarise(header_text, locations, skip_successful)


def summarise_org(org, skip_successful) -> str:
    header_text = f"Workflows for {org} repos"
    locations = [f"{org}/{repo}" for repo in config.REPOS[org]]
    return _summarise(header_text, locations, skip_successful)


def _get_command_line_args():  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--target")
    parser.add_argument("--key", action="store_true", default=False)
    parser.add_argument("--skip-successful", action="store_true", default=False)
    return vars(parser.parse_args())


def parse_args():
    args = _get_command_line_args()
    if args.pop("key", False):
        return None

    if "target" not in args:
        raise ValueError("Argument --target is required")

    # Parse target, which can either be org or org/repo
    target = args.pop("target").split("/")
    if len(target) not in [1, 2]:
        raise ValueError("Argument must be in the format org or org/repo")
    args["org"] = config.SHORTHANDS.get(target[0], target[0])
    args["repo"] = target[1] if len(target) == 2 else None
    return args


def get_text_blocks_for_key():
    blocks = get_basic_header_and_text_blocks(
        header_text="Workflow status emoji key",
        texts=[f"{v}={k.title()}" for k, v in EMOJI.items()],
    )
    return json.dumps(blocks)


def main(org, repo, skip_successful=False) -> str:
    # skip_successful skips "successful (i.e. all green)" repos is only used for summary functions
    if org == "all":
        # Summarise status for all repos in all orgs
        return summarise_all(skip_successful)
    elif org in config.REPOS.keys():  # Valid organisation
        if repo is None:
            # Summarise status for multiple repos in an org
            return summarise_org(org, skip_successful)
        # Single repo usage: Report status for all workflows in a specified repo
        return RepoWorkflowReporter(f"{org}/{repo}").report()
    else:
        return report_invalid_org(org)


if __name__ == "__main__":
    args = parse_args()
    if args is None:
        print(get_text_blocks_for_key())
    else:
        print(main(**args))

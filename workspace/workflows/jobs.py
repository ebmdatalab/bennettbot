import argparse
import json
import os
from urllib.parse import urljoin

import requests

from bennettbot import settings
from workspace.utils.blocks import (
    get_basic_header_and_text_blocks,
    get_header_block,
    get_text_block,
)
from workspace.workflows import config


TOKEN = os.environ["DATA_TEAM_GITHUB_API_TOKEN"]  # requires "read:project" and "repo"


def report_invalid_org(org):
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


class RepoWorkflowReporter:
    EMOJI = {
        "success": ":large_green_circle:",
        "running": ":large_yellow_circle:",
        "failure": ":red_circle:",
        "skipped": ":white_circle:",
        "cancelled": ":heavy_multiplication_x:",
        "missing": ":ghost:",
        "other": ":grey_question:",
    }
    EMOJI_KEY = " / ".join([f"{v}={k.title()}" for k, v in EMOJI.items()])

    def __init__(self, org_name, repo_name, branch="main"):
        """
        Retrieves and reports on the status of workflow runs in a specified repo.

        Creating an instance of this class will automatically call the GitHub API to get a list of workflow IDs and their names.
        Subsequently calling report() or summarise() will call a different endpoint of the API to get the status and conclusion for the most recent run of each workflow.

        The statuses of workflows are represented by emojis, as defined in the EMOJI class attribute.
        report() will return a full JSON message with blocks for each workflow;
        summarise() will return a single block with a summary of all workflows, which can be concatenated with other summaries.

        Parameters:
            org_name: str
                The name of the GitHib organisation that owns the repo
            repo_name: str
                The name of the repo
            branch: str
                The branch to check the status of workflows on.
                Default is "main" (as there is currently little application for anything other than main).
        """
        self.org_name = org_name
        self.repo_name = repo_name
        self.branch = branch

        self.location = f"{org_name}/{repo_name}"
        self.base_api_url = f"https://api.github.com/repos/{self.location}/"
        self.github_actions_link = (
            f"https://github.com/{self.location}/actions?query=branch%3A{self.branch}"
        )

        self.workflows = self.get_workflows()  # Dict of workflow_id: workflow_name
        self.workflow_ids = set(self.workflows.keys())

    def _get_json_response(self, path, params=None):
        url = urljoin(self.base_api_url, path)
        return get_api_result_as_json(url, params)

    def get_workflows(self) -> dict:
        results = self._get_json_response("actions/workflows")["workflows"]
        workflows = {wf["id"]: wf["name"] for wf in results}
        if self.branch is not None and self.branch == "main":
            self.remove_workflows_skipped_on_main(workflows)
        return workflows

    def remove_workflows_skipped_on_main(self, workflows):
        skipped = config.SKIPPED_WORKFLOWS_ON_MAIN.get(self.location, [])
        for workflow_id in skipped:
            workflows.pop(workflow_id, None)

    def get_all_runs(self) -> list:
        params = {"branch": self.branch} if self.branch else {}
        params["per_page"] = 50
        return self._get_json_response("actions/runs", params=params)["workflow_runs"]

    def get_latest_conclusions(self) -> dict:
        all_runs = self.get_all_runs()
        latest_runs, missing_ids = self.find_latest_for_each_workflow(all_runs)
        conclusions = {
            run["workflow_id"]: self.get_conclusion_for_run(run) for run in latest_runs
        }
        missing = {workflow_id: "missing" for workflow_id in missing_ids}
        conclusions.update(missing)
        return conclusions

    @staticmethod
    def get_conclusion_for_run(run) -> str:
        aliases = {"in_progress": "running"}
        if run["conclusion"] is None:
            status = str(str(run["status"]))
            return aliases.get(status, status)
        return str(run["conclusion"])

    def get_emoji(self, conclusion) -> str:
        return self.EMOJI.get(conclusion, self.EMOJI["other"])

    def report(self) -> str:
        def format_text(workflow_id, conclusion) -> str:
            name = self.workflows[workflow_id]
            emoji = self.get_emoji(conclusion)
            return f"{name}: {emoji} {conclusion.title().replace('_', ' ')}"

        conclusions = self.get_latest_conclusions()
        lines = [format_text(wf, conclusion) for wf, conclusion in conclusions.items()]
        blocks = [
            get_header_block(f"Workflows for {self.location}"),
            get_text_block("\n".join(lines)),  # Show in one block for compactness
            get_text_block(f"<{self.github_actions_link}|View Github Actions>"),
        ]
        return json.dumps(blocks)

    def summarise(self) -> str:
        conclusions = self.get_latest_conclusions()
        emojis = "".join([self.get_emoji(c) for c in conclusions.values()])
        link = f"<{self.github_actions_link}|link>"
        return get_text_block(f"{self.location}: {emojis} ({link})")

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
        # Some workflows were not found in the last ~1000 runs on this branch
        missing_ids = self.workflow_ids - found_ids
        return latest_runs, missing_ids


def summarise_all(branch):
    blocks = [
        get_header_block("Workflows for key repos"),
        get_text_block(RepoWorkflowReporter.EMOJI_KEY),
    ]
    # Double for loop necessary since "org" and "repo" will both vary
    for org, repos in config.REPOS.items():
        for repo in repos:
            blocks.append(RepoWorkflowReporter(org, repo, branch).summarise())
    return json.dumps(blocks)


def summarise_org(org, branch):
    blocks = [
        get_header_block(f"Workflows for {org} repos"),
        get_text_block(RepoWorkflowReporter.EMOJI_KEY),
    ]
    for repo in config.REPOS[org]:
        blocks.append(RepoWorkflowReporter(org, repo, branch).summarise())
    return json.dumps(blocks)


def _get_command_line_args():  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--branch", default="main")
    return vars(parser.parse_args())


def parse_args():
    args = _get_command_line_args()
    # Parse target, which can either be org or org/repo
    target = args.pop("target").split("/")
    if len(target) not in [1, 2]:
        raise ValueError("Argument must be in the format org or org/repo")
    args["org"] = config.SHORTHANDS.get(target[0], target[0])
    args["repo"] = target[1] if len(target) == 2 else None
    return args


def main(org, repo, branch):
    if org == "all":
        # Summarise status for all repos in all orgs
        return summarise_all(branch)
    elif org in config.REPOS.keys():  # Valid organisation
        if repo is None:
            # Summarise status for multiple repos in an org
            return summarise_org(org, branch)
        # Single repo usage: Report status for all workflows in a specified repo
        return RepoWorkflowReporter(org, repo, branch).report()
    else:
        return report_invalid_org(org)


if __name__ == "__main__":
    args = parse_args()
    print(main(**args))

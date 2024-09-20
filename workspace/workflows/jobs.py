import argparse
import json
import os

import requests

from ebmbot import settings
from workspace.utils.blocks import (
    get_basic_header_and_text_blocks,
    get_header_block,
    get_text_block,
)


TOKEN = os.environ["DATA_TEAM_GITHUB_API_TOKEN"]  # requires "read:project" and "repo"


# TODO:Make this a shared function
def get_api_result_as_json(url: str, params: dict) -> dict:  #  pragma: no cover
    headers = {"Authorization": f"Bearer {TOKEN}"}
    prms = {**params, **{"format": "json"}}
    response = requests.get(url, headers=headers, params=prms)
    response.raise_for_status()
    return response.json()


class WorkflowReporter:
    EMOJI = {
        "success": ":large_green_circle:",
        "failure": ":red_circle:",
        "skipped": ":white_circle:",
        "other": ":grey_question:",
    }

    def __init__(self, org_name, repo_name):
        self.org_name = org_name
        self.repo_name = repo_name
        self.location = f"{org_name}/{repo_name}"
        self.github_actions_link = f"https://github.com/{self.location}/actions"
        self.workflows = self.get_workflows()
        self.workflow_ids = set(self.workflows.keys())

    def get_workflows_json_from_github(self) -> dict:
        url = f"https://api.github.com/repos/{self.location}/actions/workflows"
        return get_api_result_as_json(url, params={})["workflows"]

    def get_workflows(self) -> dict:
        results = self.get_workflows_json_from_github()
        workflows = {wf["id"]: wf["name"] for wf in results}
        return workflows

    def get_all_runs(self, branch) -> list:
        url = f"https://api.github.com/repos/{self.location}/actions/runs"
        params = {"branch": branch} if branch else {}
        return get_api_result_as_json(url, params)["workflow_runs"]

    def get_latest_runs(self, branch) -> list:  # pragma: no cover
        all_runs = self.get_all_runs(branch)
        latest_runs = self.filter_for_latest_of_each_workflow(all_runs)
        return latest_runs

    def get_latest_conclusions(self, branch) -> dict:
        latest_runs = self.get_latest_runs(branch)
        return {run["workflow_id"]: run["conclusion"] for run in latest_runs}

    def report(self, detailed: bool, branch="main") -> str:
        if not detailed:
            return json.dumps([self.summarize(branch)])
        return self._report(branch)

    def _report(self, branch) -> str:
        conclusions = self.get_latest_conclusions(branch)
        lines = [
            self.get_text_reporting_workflow(wf_id, conc)
            for wf_id, conc in conclusions.items()
        ]
        blocks = [
            get_header_block(f"Workflows for {self.location}"),
            get_text_block("\n".join(lines)),  # Show in one block for compactness
            self.get_block_linking_to_gh_actions(),
        ]
        return json.dumps(blocks)

    def summarize(self, branch) -> str:
        conclusions = self.get_latest_conclusions(branch)
        emojis = "".join([self.get_emoji(c) for c in conclusions.values()])
        link = f"<{self.github_actions_link}|{self.location}>"
        return get_text_block(f"{link}: {emojis}")

    def get_block_linking_to_gh_actions(self):
        return get_text_block(f"<{self.github_actions_link}|View Github Actions>")

    def get_emoji(self, conclusion) -> str:
        return self.EMOJI.get(conclusion, self.EMOJI["other"])

    def get_text_reporting_workflow(self, workflow_id, conclusion) -> str:
        name = self.workflows[workflow_id]
        emoji = self.get_emoji(conclusion)
        return f"{name}: {str(conclusion).title()} {emoji}"

    def filter_for_latest_of_each_workflow(self, all_runs) -> list:
        latest_runs = []
        run_id = 0
        found_ids = set()
        while found_ids != self.workflow_ids and run_id < len(all_runs):
            run = all_runs[run_id]
            run_id += 1
            if run["workflow_id"] in found_ids:
                continue
            latest_runs.append(run)
            found_ids.add(run["workflow_id"])
        return latest_runs

    @staticmethod
    def get_emoji_key() -> str:  # pragma: no cover
        return " / ".join(
            [f"{v}={k.title()}" for k, v in WorkflowReporter.EMOJI.items()]
        )


def summarize_org(org, branch) -> list:
    try:
        blocks = [
            get_header_block(f"Workflows for {org}"),
            get_text_block(WorkflowReporter.get_emoji_key()),
        ]
        for repo in settings.REPOS[org]:
            blocks.append(WorkflowReporter(org, repo).summarize(branch=branch))
        return json.dumps(blocks)
    except KeyError:
        blocks = get_basic_header_and_text_blocks(
            header_text=f"No repos specified for {org}",
            texts=[
                "Use one of the following commands to report a specific repo:",
                "```report workflows [org] [repo]```",
                "```report workflows-actions [org] [repo]```",
            ],
        )
        return json.dumps(blocks)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--detailed", default=False, action="store_true")
    parser.add_argument("--branch", default="main")
    args = vars(parser.parse_args())
    # Parse target, which can either be org or org/repo
    target = args.pop("target").split("/")
    if len(target) not in [1, 2]:
        raise ValueError("Argument must be in the format org or org/repo")
    args["org"] = target[0]
    args["repo"] = target[1] if len(target) == 2 else None
    return args


def main(org, repo, detailed, branch):  # pragma: no cover
    if repo is not None:
        reporter = WorkflowReporter(org, repo)
        return reporter.report(detailed, branch=branch)
    return summarize_org(org, branch)


if __name__ == "__main__":
    args = parse_args()
    print(main(**args))

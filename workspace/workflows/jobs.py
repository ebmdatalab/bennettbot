import argparse
import json
import os
import warnings

import requests

from ebmbot import settings
from workspace.utils.blocks import (
    get_basic_header_and_text_blocks,
    get_header_block,
    get_text_block,
)


def load_config():
    path = settings.APPLICATION_ROOT / "workspace" / "workflows" / "config.json"
    return json.loads(path.read_text())


def match_shorthand(org):
    return load_config()["shorthands"].get(org, org)


def get_organization_repos(org):
    return load_config()["repos"][org]


def alias_status(status):
    return load_config()["status_aliases"].get(status, status)


TOKEN = os.environ["DATA_TEAM_GITHUB_API_TOKEN"]  # requires "read:project" and "repo"


# TODO:Make this a shared function
def get_api_result_as_json(url: str, params: dict) -> dict:  #  pragma: no cover
    headers = {"Authorization": f"Bearer {TOKEN}"}
    prms = {**params, **{"format": "json"}}
    response = requests.get(url, headers=headers, params=prms)
    response.raise_for_status()
    return response.json()


class WorkflowReporter:
    EMOJI = load_config()["emoji"]

    def __init__(self, org_name, repo_name, branch="main"):
        self.org_name = org_name
        self.repo_name = repo_name
        # Little application for anything other than main, so default to that
        self.branch = branch
        self.location = f"{org_name}/{repo_name}"
        self.github_actions_link = (
            f"https://github.com/{self.location}/actions?query=branch%3A{self.branch}"
        )
        self.workflows = self.get_workflows()
        self.workflow_ids = set(self.workflows.keys())

    def get_workflows_json_from_github(self) -> dict:
        url = f"https://api.github.com/repos/{self.location}/actions/workflows"
        return get_api_result_as_json(url, params={})["workflows"]

    def get_workflows(self) -> dict:
        results = self.get_workflows_json_from_github()
        workflows = {wf["id"]: wf["name"] for wf in results}
        if self.branch is not None and self.branch == "main":
            self.remove_workflows_skipped_on_main(workflows)
        return workflows

    def remove_workflows_skipped_on_main(self, workflows):
        skipped = load_config()["skipped_workflows_on_main"].get(self.location, [])
        for workflow_id in skipped:
            workflows.pop(workflow_id, None)

    def get_all_runs(self) -> list:
        url = f"https://api.github.com/repos/{self.location}/actions/runs"
        params = {"branch": self.branch} if self.branch else {}
        return get_api_result_as_json(url, params)["workflow_runs"]

    def get_latest_runs(self) -> list:
        all_runs = self.get_all_runs()
        latest_runs = self.filter_for_latest_of_each_workflow(all_runs)
        return latest_runs

    def get_latest_conclusions(self) -> dict:
        latest_runs = self.get_latest_runs()
        return {
            run["workflow_id"]: self.get_conclusion_for_run(run) for run in latest_runs
        }

    @staticmethod
    def get_conclusion_for_run(run):
        if run["conclusion"] is None:
            return alias_status(str(run["status"]))
        return str(run["conclusion"])

    def report(self, detailed: bool) -> str:
        if not detailed:
            return json.dumps([self.summarize()])
        return self._report()

    def _report(self) -> str:
        conclusions = self.get_latest_conclusions()
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

    def summarize(self) -> str:
        conclusions = self.get_latest_conclusions()
        emojis = "".join([self.get_emoji(c) for c in conclusions.values()])
        link = f"<{self.github_actions_link}|link>"
        return get_text_block(f"{self.location}: {emojis} ({link})")

    def get_block_linking_to_gh_actions(self):
        return get_text_block(f"<{self.github_actions_link}|View Github Actions>")

    def get_emoji(self, conclusion) -> str:
        return self.EMOJI.get(conclusion, self.EMOJI["other"])

    def get_text_reporting_workflow(self, workflow_id, conclusion) -> str:
        name = self.workflows[workflow_id]
        emoji = self.get_emoji(conclusion)
        return f"{name}: {emoji} {conclusion.title().replace('_', ' ')}"

    def filter_for_latest_of_each_workflow(self, all_runs) -> list:
        latest_runs = []
        run_id = 0
        found_ids = set()
        while found_ids != self.workflow_ids and run_id <= len(all_runs):
            if run_id == len(all_runs):
                self.warn_about_missing_ids(found_ids)
                break
            run = all_runs[run_id]
            run_id += 1
            if run["workflow_id"] in found_ids:
                continue
            latest_runs.append(run)
            found_ids.add(run["workflow_id"])
        return latest_runs

    def warn_about_missing_ids(self, found_ids):
        missing_ids = self.workflow_ids - found_ids
        missing = "\n".join([f"{i}={self.workflows[i]}" for i in missing_ids])
        message = f"Missing IDs for {self.location}: \n{missing}."
        warnings.warn(message=message, category=UserWarning)

    @staticmethod
    def get_emoji_key() -> str:
        return " / ".join(
            [f"{v}={k.title()}" for k, v in WorkflowReporter.EMOJI.items()]
        )


def summarize_org(org, branch) -> list:
    try:
        return _summarize_org(org, branch)
    except KeyError:
        return request_user_to_specify_repo(org)


def _summarize_org(org, branch):
    repos = get_organization_repos(org)
    blocks = [
        get_header_block(f"Workflows for {org}"),
        get_text_block(WorkflowReporter.get_emoji_key()),
    ]
    for repo in repos:
        blocks.append(WorkflowReporter(org, repo, branch).summarize())
    return json.dumps(blocks)


def request_user_to_specify_repo(org):
    blocks = get_basic_header_and_text_blocks(
        header_text=f"No repos specified for {org}",
        texts=[
            "Use one of the following commands to report a specific repo (provided in the form of `org/repo`):",
            "```workflows show [repo]```",
            "```workflows show-actions [repo]```",
        ],
    )
    return json.dumps(blocks)


def _get_command_line_args():  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--detailed", default=False, action="store_true")
    parser.add_argument("--branch", default="main")
    return vars(parser.parse_args())


def parse_args():
    args = _get_command_line_args()
    # Parse target, which can either be org or org/repo
    target = args.pop("target").split("/")
    if len(target) not in [1, 2]:
        raise ValueError("Argument must be in the format org or org/repo")
    args["org"] = match_shorthand(target[0])
    args["repo"] = target[1] if len(target) == 2 else None
    return args


def main(org, repo, detailed, branch):
    if repo is not None:
        reporter = WorkflowReporter(org, repo, branch)
        return reporter.report(detailed)
    return summarize_org(org, branch)


if __name__ == "__main__":
    args = parse_args()
    print(main(**args))

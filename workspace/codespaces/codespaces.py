"""
Queries the GitHub REST API "List Codespaces for the organization" endpoint
and shows the Codespaces that are at risk of being deleted.
"""

import collections
import datetime
import json
import os

import requests

from workspace.utils import blocks


URL_PATTERN = "https://api.github.com/orgs/{org}/codespaces"
# The following can be a classic PAT with the admin:org scope or a fine-grained token
# with "Codespaces" repository permissions set to "read" and "Organization codespaces"
# organization permissions set to "read". For more information, see:
# https://docs.github.com/en/rest/codespaces/organizations?apiVersion=2022-11-28#list-codespaces-for-the-organization
TOKEN = os.environ["CODESPACES_GITHUB_API_TOKEN"]
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


Codespace = collections.namedtuple(
    "Codespace",
    ["last_used_days_ago", "owner", "name", "has_unpushed", "has_uncommitted"],
)


def fetch(url, key):
    """
    Recursively fetch all records from the GitHub REST API endpoint given by `url`.
    `key` is the property under which the records are stored.
    """

    def set_bearer_auth(request):
        request.headers["Authorization"] = f"Bearer {TOKEN}"
        return request

    def fetch_one_page(page_url):
        response = requests.get(page_url, auth=set_bearer_auth, headers=HEADERS)
        response.raise_for_status()
        yield from response.json().get(key)
        if "next" in response.links:
            yield from fetch_one_page(response.links["next"]["url"])

    yield from fetch_one_page(url)


def get_codespace(record):
    now = datetime.datetime.now(datetime.timezone.utc)
    last_used_at = datetime.datetime.fromisoformat(record["last_used_at"])
    return Codespace(
        last_used_days_ago=(now - last_used_at).days,
        owner=record["owner"]["login"],
        name=record["name"],
        has_uncommitted=record["git_status"]["has_uncommitted_changes"],
        has_unpushed=record["git_status"]["has_unpushed_changes"],
    )


def is_at_risk(codespace, threshold_in_days):
    is_dormant = codespace.last_used_days_ago >= threshold_in_days
    return is_dormant and (codespace.has_unpushed or codespace.has_uncommitted)


def main():
    org = "opensafely"
    threshold_in_days = 20

    records = fetch(URL_PATTERN.format(org=org), "codespaces")
    codespaces = (get_codespace(rec) for rec in records)
    at_risk_codespaces = sorted(
        (cs for cs in codespaces if is_at_risk(cs, threshold_in_days)),
        key=lambda cs: cs.last_used_days_ago,
        reverse=True,
    )

    if at_risk_codespaces:
        items = [
            (
                f"* `{cs.owner}` | "
                f"last used {cs.last_used_days_ago} days ago | "
                f"**id**: `{cs.name}` | "
                f"**Uncommitted**: {'Yes' if cs.has_uncommitted else 'No'} | "
                f"**Unpushed**: {'Yes' if cs.has_unpushed else 'No'}\n"
            )
            for cs in at_risk_codespaces
        ]
        body = f"The following `{org}` Codespaces are at risk of deletion.\n\n"
        body += "".join(items)
    else:
        body = f"No `{org}` Codespaces are at risk of deletion :tada:"

    header = "Codespaces Report"
    return json.dumps(blocks.get_basic_header_and_text_blocks(header, body))


if __name__ == "__main__":
    from pprint import pprint

    pprint(json.loads(main()))

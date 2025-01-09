"""
Queries the GitHub REST API "List Codespaces for the organization" endpoint
and shows the Codespaces that are "at risk" of being deleted, defined as having
uncommitted or unpushed changes and the retention period expiry being within
some threshold.

Refer to the codespaces playbook in the team manual for how this is used.
As of 2025-01, that's located at:
https://github.com/ebmdatalab/team-manual/blob/main/docs/tech-group/playbooks/codespaces.md
"""

import collections
import datetime
import json
import os

import requests
from slack_sdk.models.blocks import (
    HeaderBlock,
    RichTextBlock,
    RichTextElementParts,
    RichTextListElement,
    RichTextSectionElement,
)


CODE = RichTextElementParts.TextStyle(code=True)
BOLD = RichTextElementParts.TextStyle(bold=True)
Text = RichTextElementParts.Text


URL_PATTERN = "https://api.github.com/orgs/{org}/codespaces"
# The following can be a classic PAT with the admin:org scope or a fine-grained token
# with "Codespaces" repository permissions set to "read" and "Organization codespaces"
# organization permissions set to "read". For more information, see:
# https://docs.github.com/en/rest/codespaces/organizations?apiVersion=2022-11-28#list-codespaces-for-the-organization
# Someone with admin permissions on the organization needs to do this.
# For the opensafely org, created PATs should be stored in BitWarden.
TOKEN = os.environ["CODESPACES_GITHUB_API_TOKEN"]
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


Codespace = collections.namedtuple(
    "Codespace",
    [
        "owner",
        "name",
        "repo",
        "retention_expires_at",
        "remaining_retention_period_days",
        "retention_period_days",
        "has_uncommitted",
        "has_unpushed",
    ],
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
    if record["retention_expires_at"]:
        retention_expires_at = datetime.datetime.fromisoformat(
            record["retention_expires_at"]
        )
        now = datetime.datetime.now(retention_expires_at.tzinfo)
        # This "rounds down", eg 10.7 days will be reported as 10 days as it
        # throws aways the parts smaller than one day. This seems fine.
        remaining_retention_period_days = (retention_expires_at - now).days
    else:
        # Codespaces may not have a retention period if the user has manually
        # chosen to keep the codespace indefinitely, which we allow. Also very
        # new codespaces may not have this set by GitHub yet. Don't report.
        retention_expires_at = None
        remaining_retention_period_days = None

    if record["retention_period_minutes"]:
        minutes_per_day = 60 * 24  # 60m per hour, 24 hours per day.
        # This could be rounded down to 0 if set to less than a day. Probably
        # nobody will do this, but if they do they're out of scope, as we have
        # little chance of warning them usefully.
        retention_period_days = record["retention_period_minutes"] // minutes_per_day
    else:
        # The user has manually chosen to keep the codespace indefinitely.
        retention_period_days = None

    return Codespace(
        owner=record["owner"]["login"],
        name=record["name"],
        repo=record["repository"]["name"],
        retention_expires_at=retention_expires_at,
        remaining_retention_period_days=remaining_retention_period_days,
        retention_period_days=retention_period_days,
        has_uncommitted=record["git_status"]["has_uncommitted_changes"],
        has_unpushed=record["git_status"]["has_unpushed_changes"],
    )


def is_at_risk(codespace, threshold_in_days):
    if codespace.remaining_retention_period_days is not None:
        close_to_expiry = codespace.remaining_retention_period_days <= threshold_in_days
        return close_to_expiry and (codespace.has_unpushed or codespace.has_uncommitted)
    else:
        # The user has manually chosen to keep the codespace indefinitely,
        # therefore there's no risk of them losing their work.
        return False


def main():
    org = "opensafely"
    # Arbitrary threshold. Gives us a bit more than a week to respond.
    threshold_in_days = 10

    records = fetch(URL_PATTERN.format(org=org), "codespaces")
    codespaces = (get_codespace(rec) for rec in records)
    at_risk_codespaces = sorted(
        (cs for cs in codespaces if is_at_risk(cs, threshold_in_days)),
        key=lambda cs: cs.remaining_retention_period_days,
    )

    if at_risk_codespaces:
        intro_block = RichTextSectionElement(
            elements=[
                Text(text=org, style=CODE),
                Text(
                    text=(
                        " Codespaces with unsaved work at risk (expiring within "
                        f"{threshold_in_days} days):"
                    )
                ),
            ]
        )

        list_items = [
            RichTextSectionElement(
                elements=[
                    Text(text=cs.owner, style=CODE),
                    Text(text=f" on {cs.retention_expires_at:%A, %b %d at %H:%M}"),
                    Text(text=f" ({remaining_days_text}) "),
                    Text(text="repo", style=BOLD),
                    Text(text=": "),
                    Text(text=cs.repo, style=CODE),
                    Text(text=" ID", style=BOLD),
                    Text(text=": "),
                    Text(text=cs.name, style=CODE),
                    Text(text=" Retention", style=BOLD),
                    Text(text=f": {cs.retention_period_days} days "),
                    Text(text="Uncommitted", style=BOLD),
                    Text(text=f": {'Yes' if cs.has_uncommitted else 'No'} "),
                    Text(text="Unpushed", style=BOLD),
                    Text(text=f": {'Yes' if cs.has_unpushed else 'No'}"),
                ]
            )
            for cs in at_risk_codespaces
            if (
                remaining_days_text := (
                    "<1 day"
                    if not cs.remaining_retention_period_days
                    else str(cs.remaining_retention_period_days) + " days"
                )
            )
        ]
    else:
        intro_block = RichTextSectionElement(
            elements=[
                Text(text="No "),
                Text(text=org, style=CODE),
                Text(
                    text=(
                        " Codespaces with unsaved work at risk (expiring within "
                        f"{threshold_in_days} days) :tada:"
                    )
                ),
            ]
        )
        list_items = []

    return json.dumps(
        [
            HeaderBlock(text="Codespaces at risk report").to_dict(),
            RichTextBlock(
                elements=[
                    intro_block,
                    RichTextListElement(elements=list_items, style="bullet"),
                ]
            ).to_dict(),
        ],
        indent=2,
    )


if __name__ == "__main__":
    print(main())

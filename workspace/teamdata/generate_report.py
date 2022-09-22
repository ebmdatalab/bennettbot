import json
import os

import requests


URL = "https://api.github.com/graphql"
TOKEN = os.environ["DATA_TEAM_GITHUB_API_TOKEN"]  # requires "read:project" and "repo"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}",
    "GraphQL-Features": "projects_next_graphql",
}
ORG_NAME = "opensafely-core"
PROJECT_NUM = 13


def main():
    project_id = get_project_id()
    cards = get_project_cards(project_id)

    tickets_by_status = {
        "Under Review": [],
        "Blocked": [],
        "In Progress": [],
    }

    for card in cards:
        status, summary = get_status_and_summary(card)
        if status not in tickets_by_status:
            continue
        tickets_by_status[status].append(summary)

    # report_output = ["[Project Board Summary](https://github.com/orgs/opensafely-core/projects/13/views/1)\n"]

    report_output = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":newspaper: Project Board Summary :newspaper:",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<https://github.com/orgs/opensafely-core/projects/13/views/1>",
            },
        },
    ]

    for status, tickets in tickets_by_status.items():

        report_output.extend(
            [
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{status}*"},
                },
            ]
        )
        ticket_sections = [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"• {ticket}"}}
            for ticket in tickets
        ]
        report_output.extend(ticket_sections)

    return json.dumps(report_output)


def get_project_id():
    query = """
    query projectId($org_name: String!, $project_num: Int!) {
      organization(login: $org_name) {
        projectV2(number: $project_num) {
          id
          title
        }
      }
    }
    """
    variables = {
        "org_name": ORG_NAME,
        "project_num": PROJECT_NUM,
    }

    payload = {"query": query, "variables": variables}
    rsp = requests.post(URL, headers=HEADERS, json=payload)
    rsp.raise_for_status()
    return rsp.json()["data"]["organization"]["projectV2"]["id"]


def get_project_cards(project_id):
    query = """
    query projectCards($project_id: ID!) {
      node(id: $project_id) {
        ... on ProjectV2 {
          items(first: 100) {
            nodes {
              fieldValues(last: 100) {
                nodes {
                  ... on ProjectV2ItemFieldSingleSelectValue {
                    name
                    field {
                      ... on ProjectV2FieldCommon {
                        name
                      }
                    }
                  }
                }
              }
              content {
                ... on DraftIssue {
                  title
                  assignees(first: 10) {
                    nodes {
                      login
                    }
                  }
                }
                ... on Issue {
                  title
                  bodyUrl
                  assignees(first: 10) {
                    nodes {
                      login
                    }
                  }
                }
                ... on PullRequest {
                  title
                  assignees(first: 10) {
                    nodes {
                      login
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    variables = {"project_id": project_id}
    payload = {"query": query, "variables": variables}
    rsp = requests.post(URL, headers=HEADERS, json=payload)
    rsp.raise_for_status()
    data = rsp.json()

    return sorted(
        data["data"]["node"]["items"]["nodes"],
        key=lambda card: card["content"]["title"],
    )


def get_slack_username(github_username):
    return {
        "CarolineMorton": "<@Caroline>",
        "Jongmassey": "<@Jon>",
        "StevenMaude": "<@Steve>",
        "evansd": "<@dave>",
        "iaindillingham": "<@Iain>",
        "inglesp": "<@inglesp>",
        "milanwiedemann": "<@Milan>",
        "rebkwok": "<@Becky S>",
        "robinyjpark": "<@Robin>",
    }.get(github_username) or f"<@{github_username}>"


def get_status_and_summary(card):
    status = card["fieldValues"]["nodes"][-1]["name"]
    title = card["content"]["title"]
    url = card["content"].get("bodyUrl")
    assignees = " / ".join(
        get_slack_username(node["login"])
        for node in card["content"]["assignees"]["nodes"]
    )

    if url:
        summary = f"<{url}|{title}>"
    else:
        summary = title

    if assignees:
        summary = f"{summary} ({assignees})"

    return status, summary


if __name__ == "__main__":
    main()

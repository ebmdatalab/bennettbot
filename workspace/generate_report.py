import argparse
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


def post_request(payload):  # pragma: no cover
    rsp = requests.post(URL, headers=HEADERS, json=payload)
    rsp.raise_for_status()
    return rsp.json()


def main(project_num, statuses):
    project_id = get_project_id(int(project_num))
    cards = get_project_cards(project_id)
    tickets_by_status = {status: [] for status in statuses}

    for card in cards:  # pragma: no cover
        status, summary = get_status_and_summary(card)
        if status and status in statuses:
            tickets_by_status[status].append(summary)

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
                "text": f"<https://github.com/orgs/opensafely-core/projects/{project_num}/views/1>",
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


def get_project_id(project_num):
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
        "project_num": project_num,
    }

    payload = {"query": query, "variables": variables}
    rsp = post_request(payload)
    return rsp["data"]["organization"]["projectV2"]["id"]


def get_project_cards(project_id):
    query = """
    query projectCards($project_id: ID!, $cursor: String) {
      node(id: $project_id) {
        ... on ProjectV2 {
          items(first: 100, after: $cursor) {
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
            pageInfo {
              endCursor
              hasNextPage
            }
          }
        }
      }
    }
    """

    cursor = None
    project_data = []
    while True:
        variables = {"project_id": project_id, "cursor": cursor}
        payload = {"query": query, "variables": variables}
        data = post_request(payload)
        node_data = data["data"]["node"]["items"]
        project_data.extend(node_data["nodes"])
        if not node_data["pageInfo"]["hasNextPage"]:
            break
        # update the cursor we pass into the GraphQL query
        cursor = node_data["pageInfo"]["endCursor"]  # pragma: no cover

    return sorted(
        project_data,
        key=lambda card: card["content"]["title"],
    )  # pragma: no cover


def get_slack_username(github_username):
    return {
        "CarolineMorton": "<@UMMDD4V2P>",
        "Jongmassey": "<@U023ZG5H24R>",
        "StevenMaude": "<@U01TJP3CG76>",
        "evansd": "<@UAXE5V4RG>",
        "iaindillingham": "<@U01S6BLGK28>",
        "inglesp": "<@U4N1YPAP7>",
        "milanwiedemann": "<@U02GPV8NNU9>",
        "rebkwok": "<@U01SP5JLBFD>",
        "robinyjpark": "<@U021UP18T52>",
        "LisaHopcroft": "<@U029ER915GX>",
        "lucyb": "<@U035FT48KEK>",
        "CLStables": "<@U036A6LTR7D>",
        "tomodwyer": "<@U01UQ0T2M7V>",
        "bloodearnest": "<@U01AMBZUT47>",
        "ghickman": "ghickman",  # George doesn't want to receive Slack notifications
        "madwort": "<@U019R5FJ7G8>",
        "benbc": "<@U01SPCP06Q1>",
    }.get(github_username) or f"<@{github_username}>"


def get_status_and_summary(card):  # pragma: no cover
    if not card["fieldValues"]["nodes"][-1]:
        return (None, None)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-num", help="The GitHub Project number", type=int)
    parser.add_argument("--statuses", nargs="+", help="List of GitHub Project statuses")
    args = parser.parse_args()
    print(main(args.project_num, args.statuses))

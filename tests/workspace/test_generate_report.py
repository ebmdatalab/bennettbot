import json

from workspace import generate_report


def test_generate_report():
    def mock_post_request(payload):
        return {
            "data": {
                "organization": {"projectV2": {"id": 1}},
                "node": {
                    "items": {
                        "nodes": "",
                        "pageInfo": {"hasNextPage": False, "endCursor": "abc"},
                    }
                },
            }
        }

    generate_report.post_request = mock_post_request

    response = [
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
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Under Review*"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*Blocked*"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": "*In Progress*"}},
    ]

    statuses = ["Under Review", "Blocked", "In Progress"]
    assert generate_report.main(13, statuses) == json.dumps(response)


def test_get_slack_username_returns_github_user_by_default():
    result = generate_report.get_slack_username("test user")

    assert result == "<@test user>"


def test_get_slack_username_returns_slack_user_id():
    result = generate_report.get_slack_username("lucyb")

    assert result == "<@U035FT48KEK>"

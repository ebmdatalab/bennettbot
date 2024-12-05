import workspace.utils.people


def test_get_slack_username_returns_slack_user_id():
    result = workspace.utils.people.get_slack_username("lucyb")

    assert result == "<@U035FT48KEK>"


def test_get_slack_username_returns_github_user_by_default():
    result = workspace.utils.people.get_slack_username("test user")

    assert result == "<@test user>"

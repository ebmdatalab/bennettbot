from workspace.utils.people import (
    People,
    get_person_from_github_username,
)


def test_get_person_from_github_username():
    result = get_person_from_github_username("lucyb")

    assert result == People.LUCY.value


def test_get_person_from_github_username_returns_default():
    result = get_person_from_github_username("TestUser")

    assert result.human_readable == "TestUser"
    assert result.github_username == "TestUser"
    assert result.slack_username == "TestUser"


def test_get_formatted_slack_username_returns_slack_user_id():
    result = People.LUCY.value.get_formatted_slack_username()

    assert result == "<@U035FT48KEK>"

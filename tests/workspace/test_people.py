from workspace.utils.people import People


def test_get_person_from_github_username():
    result = People.by_github_username("lucyb")

    assert result == People.LUCY


def test_get_person_from_github_username_returns_default():
    result = People.by_github_username("TestUser")

    assert result.human_readable == "TestUser"
    assert result.github_username == "TestUser"
    assert result.slack_username == "TestUser"


def test_formatted_slack_username():
    result = People.LUCY.formatted_slack_username

    assert result == "<@U035FT48KEK>"

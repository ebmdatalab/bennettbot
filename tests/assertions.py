from contextlib import contextmanager
from unittest.mock import patch


def assert_job_matches(job, type_, args, slack_channel, start_after, started_at):
    assert_subdict(
        {
            "type": type_,
            "args": args,
            "slack_channel": slack_channel,
            "start_after": start_after,
            "started_at": started_at,
        },
        job,
    )


def assert_suppression_matches(suppression, job_type, start_at, end_at):
    assert_subdict(
        {"job_type": job_type, "start_at": start_at, "end_at": end_at}, suppression
    )


def assert_subdict(d1, d2):
    for k in d1:
        assert d1[k] == d2[k]


@contextmanager
def assert_slack_client_sends_messages(web_api=(), websocket=()):
    with patch("slackbot.slackclient.SlackClient.rtm_connect"):
        with patch("slackbot.slackclient.SlackClient.send_message") as p1:
            with patch("slackbot.slackclient.SlackClient.rtm_send_message") as p2:
                yield

    check_slack_client_calls(p1, web_api)
    check_slack_client_calls(p2, websocket)


def check_slack_client_calls(p, expected_calls):
    assert len(expected_calls) == len(p.call_args_list)
    for exp_call, call in zip(expected_calls, p.call_args_list):
        assert exp_call[0] == call[0][0]  # channel
        assert exp_call[1] in call[0][1]  # message
        if len(exp_call) == 3:
            assert exp_call[2] == call[1]["thread_ts"]


@contextmanager
def assert_slack_client_reacts_to_message():
    with patch("slackbot.slackclient.SlackClient.react_to_message") as p:
        yield
        assert p.call_count == 1


@contextmanager
def assert_slack_client_doesnt_react_to_message():
    with patch("slackbot.slackclient.SlackClient.react_to_message") as p:
        yield
        assert p.call_count == 0

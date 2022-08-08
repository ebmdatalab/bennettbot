from contextlib import contextmanager
from unittest.mock import patch


def assert_job_matches(job, type_, args, channel, start_after, started_at):
    assert_subdict(
        {
            "type": type_,
            "args": args,
            "channel": channel,
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
def assert_slack_client_sends_messages(messages_kwargs=None):
    messages_kwargs = messages_kwargs or {}
    with patch("slack_sdk.WebClient.chat_postMessage") as p:
        yield

    check_slack_client_calls(p, messages_kwargs)


@contextmanager
def assert_slack_client_sends_no_messages():
    with patch("slack_sdk.WebClient.chat_postMessage") as p:
        yield

    check_slack_client_calls(p, ())


def check_slack_client_calls(p, expected_messages_kwargs):
    assert len(expected_messages_kwargs) == len(p.call_args_list)    
    for exp_call_kwargs, call in zip(expected_messages_kwargs, p.call_args_list):
        for key, value in exp_call_kwargs.items():
            if key == "text":
                assert value in call.kwargs[key]
            else:
                assert call.kwargs[key] == value


@contextmanager
def assert_slack_client_reacts_to_message():
    with patch("slack_sdk.WebClient.reactions_add") as p:
        yield
        assert p.call_count == 1


@contextmanager
def assert_slack_client_doesnt_react_to_message():
    with patch("slack_sdk.WebClient.reactions_add") as p:
        yield
        assert p.call_count == 0

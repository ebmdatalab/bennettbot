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


def assert_slack_client_sends_messages(test_recorder, messages_kwargs=None):
    messages_kwargs = messages_kwargs or []
    actual_call_kwargs = test_recorder.mock_received_requests_kwargs.get(
        "/chat.postMessage", []
    )
    check_slack_client_calls(actual_call_kwargs, messages_kwargs)


@contextmanager
def assert_patched_slack_client_sends_messages(messages_kwargs=None):
    messages_kwargs = messages_kwargs or []
    with patch("slack_sdk.WebClient.chat_postMessage") as p:
        yield
    actual_call_kwargs = [call.kwargs for call in p.call_args_list]
    check_slack_client_calls(actual_call_kwargs, messages_kwargs)


def check_slack_client_calls(actual_call_kwargs_list, expected_messages_kwargs):
    assert len(expected_messages_kwargs) == len(actual_call_kwargs_list)
    for exp_call_kwargs, actual_call in zip(
        expected_messages_kwargs, actual_call_kwargs_list
    ):
        for key, value in exp_call_kwargs.items():
            if key == "text":
                assert value in actual_call[key]
            else:
                assert actual_call[key] == value


def assert_slack_client_reacts_to_message(test_recorder, reaction_count):
    assert test_recorder.mock_received_requests["/reactions.add"] == reaction_count


def assert_slack_client_doesnt_react_to_message(test_recorder):
    assert not test_recorder.mock_received_requests.get("/reactions.add")

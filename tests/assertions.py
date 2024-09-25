from .mock_http_request import get_mock_received_requests


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


def assert_running_job(job_scheduled):
    assert job_scheduled


def assert_no_running_job(job_scheuled):
    assert not job_scheuled


def assert_subdict(d1, d2):
    for k in d1:
        assert d1[k] == d2[k]


def assert_slack_client_sends_messages(messages_kwargs=None, message_format=None):
    messages_kwargs = messages_kwargs or []
    message_format = message_format or "text"
    actual_call_kwargs = get_mock_received_requests().get("/api/chat.postMessage", [])
    check_slack_client_calls(actual_call_kwargs, messages_kwargs)
    # check the format of the final message sent to slack
    if message_format == "text" and messages_kwargs:
        assert "blocks" not in actual_call_kwargs[-1]


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


def assert_slack_client_reacts_to_message(reaction_count):
    assert_call_counts({"/api/reactions.add": reaction_count})


def assert_slack_client_doesnt_react_to_message():
    requests_by_path = get_mock_received_requests()
    assert "/api/reactions.add" not in requests_by_path


def assert_call_counts(call_counts):
    requests_by_path = get_mock_received_requests()
    for path, count in call_counts.items():
        assert len(requests_by_path[path]) == count

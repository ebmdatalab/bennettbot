from workspace.utils.blocks import truncate_text


def test_truncate_text():
    original_text = "hello" * 1000
    truncated_text = truncate_text(original_text)
    assert len(truncated_text) == 3000
    assert truncated_text.endswith("...")

def get_text_block(text, block_type="section", text_type="mrkdwn"):
    return {
        "type": block_type,
        "text": {
            "type": text_type,
            "text": text,
        },
    }


def get_header_block(header_text, text_type="plain_text"):
    return get_text_block(header_text, block_type="header", text_type=text_type)


def get_basic_header_and_text_blocks(
    header_text: str, texts: list | str, text_type="mrkdwn"
):
    """
    Returns a list of blocks: a header block and text blocks with little room for customization.
    "texts" can be a list of strings or a single string; In the former case, each string will be a separate text block.
    The header block is a plain text header block.
    The text blocks have block type "section" and the text type is "mrkdwn" by default.
    """
    header_block = get_header_block(header_text)
    if isinstance(texts, str):
        texts = [texts]
    text_blocks = [get_text_block(text, text_type=text_type) for text in texts]
    return [header_block] + text_blocks

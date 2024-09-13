def get_text_block(text, block_type="section", text_type="mrkdwn"):
    return {
        "type": block_type,
        "text": {
            "type": text_type,
            "text": text,
        },
    }

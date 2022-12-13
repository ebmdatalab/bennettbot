# noqa: INP001
import json


def hello_world(name=None):
    if name:
        return f"Hello {name}!"
    return "Hello World!"


def hello_world_blocks():
    return json.dumps(
        [{"type": "section", "text": {"type": "plain_text", "text": "Hello World!"}}]
    )


def hello_world_blocks_error():
    raise Exception("An error was found!")

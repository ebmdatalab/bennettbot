import re

from slackbot.bot import respond_to


@respond_to(r'help', re.IGNORECASE)
def core_help(message):
    msg = """
`op help`: help about openprescribing
`fdaaa help`: help about fdaaa
"""
    message.reply(msg)

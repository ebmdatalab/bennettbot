def get_slack_username(github_username):
    """Get a dict mapping GitHub username to Slack username."""
    # Find a user's username by right clicking on their name in the Slack app and clicking "Copy link"
    user_id = {
        "CLStables": "U036A6LTR7D",
        "Jongmassey": "U023ZG5H24R",
        "KatieB5": "U07KUKWBGKV",
        "Mary-Anya": "U07LKQ06Q8L",
        "Providence-o": "U07AGDM6ZJN",
        "StevenMaude": "U01TJP3CG76",
        "alarthast": "U07KX6L3CMA",
        "benbc": "U01SPCP06Q1",
        "bloodearnest": "U01AMBZUT47",
        "eli-miriam": "U07LHEJ9TS4",
        "evansd": "UAXE5V4RG",
        "iaindillingham": "U01S6BLGK28",
        "inglesp": "U4N1YPAP7",
        "lucyb": "U035FT48KEK",
        "madwort": "U019R5FJ7G8",
        "milanwiedemann": "U02GPV8NNU9",
        "mikerkelly": "U07KKL4PJJY",
        "rebkwok": "U01SP5JLBFD",
        "remlapmot": "U07L0L0SS6M",
        "rw251": "U07QEMHUUMD",
        "tomodwyer": "U01UQ0T2M7V",
    }.get(github_username) or github_username
    return f"<@{user_id}>"

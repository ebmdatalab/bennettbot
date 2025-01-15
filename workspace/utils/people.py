from collections import namedtuple
from enum import Enum


Person = namedtuple("Person", ["human_readable", "github_username", "slack_username"])


class People(Enum):
    """Tech team members' GitHub and Slack usernames."""

    # Find a Slack user's username by right-clicking on their name in the Slack app and clicking "Copy link".

    ALICE = Person("Alice", "alarthast", "U07KX6L3CMA")
    BECKY = Person("Becky", "rebkwok", "U01SP5JLBFD")
    BEN_BC = Person("Ben BC", "benbc", "U01SPCP06Q1")
    CATHERINE = Person("Catherine", "CLStables", "U036A6LTR7D")
    DAVE = Person("Dave", "evansd", "UAXE5V4RG")
    ELI = Person("Eli", "eli-miriam", "U07LHEJ9TS4")
    IAIN = Person("Iain", "iaindillingham", "U01S6BLGK28")
    JON = Person("Jon", "Jongmassey", "U023ZG5H24R")
    KATIE = Person("Katie", "KatieB5", "U07KUKWBGKV")
    LUCY = Person("Lucy", "lucyb", "U035FT48KEK")
    MARY = Person("Mary", "Mary-Anya", "U07LKQ06Q8L")
    MILAN = Person("Milan", "milanwiedemann", "U02GPV8NNU9")
    MIKE = Person("Mike", "mikerkelly", "U07KKL4PJJY")
    PETER = Person("Peter", "inglesp", "U4N1YPAP7")
    PROVIDENCE = Person("Providence", "Providence-o", "U07AGDM6ZJN")
    RICHARD = Person("Richard", "rw251", "U07QEMHUUMD")
    SIMON = Person("Simon", "bloodearnest", "U01AMBZUT47")
    STEVE = Person("Steve", "StevenMaude", "U01TJP3CG76")
    THOMAS = Person("Thomas", "tomodwyer", "U01UQ0T2M7V")
    TOM_P = Person("Tom P", "remlapmot", "U07L0L0SS6M")
    TOM_W = Person("Tom W", "madwort", "U019R5FJ7G8")


PEOPLE_BY_GITHUB_USERNAME = {
    person.value.github_username: person.value for person in People
}

TEAM_REX = [
    People.JON,
    People.KATIE,
    People.LUCY,
    People.STEVE,
    People.MIKE,
    People.THOMAS,
]


def get_person_from_github_username(github_username) -> Person:
    default = Person(
        human_readable=github_username,
        github_username=github_username,
        slack_username=github_username,
    )
    return PEOPLE_BY_GITHUB_USERNAME.get(github_username, default)


def get_formatted_slack_username(person: Person) -> str:
    return f"<@{person.slack_username}>"

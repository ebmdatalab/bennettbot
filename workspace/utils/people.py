from collections import namedtuple
from enum import Enum


Person = namedtuple("Person", ["github_username", "slack_username"])


class People(Enum):
    """Tech team members' GitHub and Slack usernames."""

    # Find a Slack user's username by right-clicking on their name in the Slack app and clicking "Copy link".

    ALICE = Person("alarthast", "U07KX6L3CMA")
    BECKY = Person("rebkwok", "U01SP5JLBFD")
    BEN_BC = Person("benbc", "U01SPCP06Q1")
    CATHERINE = Person("CLStables", "U036A6LTR7D")
    DAVE = Person("evansd", "UAXE5V4RG")
    ELI = Person("eli-miriam", "U07LHEJ9TS4")
    IAIN = Person("iaindillingham", "U01S6BLGK28")
    JON = Person("Jongmassey", "U023ZG5H24R")
    KATIE = Person("KatieB5", "U07KUKWBGKV")
    LUCY = Person("lucyb", "U035FT48KEK")
    MARY = Person("Mary-Anya", "U07LKQ06Q8L")
    MILAN = Person("milanwiedemann", "U02GPV8NNU9")
    MIKE = Person("mikerkelly", "U07KKL4PJJY")
    PETER = Person("inglesp", "U4N1YPAP7")
    PROVIDENCE = Person("Providence-o", "U07AGDM6ZJN")
    RICHARD = Person("rw251", "U07QEMHUUMD")
    SIMON = Person("bloodearnest", "U01AMBZUT47")
    STEVE = Person("StevenMaude", "U01TJP3CG76")
    THOMAS = Person("tomodwyer", "U01UQ0T2M7V")
    TOM_P = Person("remlapmot", "U07L0L0SS6M")
    TOM_W = Person("madwort", "U019R5FJ7G8")


TEAM_REX = {
    People.JON,
    People.KATIE,
    People.LUCY,
    People.STEVE,
    People.MIKE,
    People.THOMAS,
}


def get_slack_username(github_username: str) -> str:
    person = (
        [p.value for p in People if p.value.github_username == github_username]
        or [Person(github_username=None, slack_username=github_username)]
    )[0]
    return get_formatted_slack_username(person)


def get_formatted_slack_username(person: Person) -> str:
    return f"<@{person.slack_username}>"

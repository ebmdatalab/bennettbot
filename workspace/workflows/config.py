SHORTHANDS = {
    "os": "opensafely",
    "osc": "opensafely-core",
    "ebm": "ebmdatalab",
}

TEAMS = [
    "Tech shared",
    "Team REX",
    "Team RAP",
]

REPOS = {
    "actions-registry": {
        "org": "opensafely-core",
        "team": "Team REX",
    },
    "airlock": {
        "org": "opensafely-core",
        "team": "Team RAP",
    },
    "backend-server": {
        "org": "opensafely-core",
        "team": "Team RAP",
    },
    "bennett.ox.ac.uk": {
        "org": "ebmdatalab",
        "team": "Team REX",
    },
    "bennettbot": {
        "org": "ebmdatalab",
        "team": "Team RAP",
    },
    "cohort-extractor": {
        "org": "opensafely-core",
        "team": "Team RAP",
    },
    "documentation": {
        "org": "opensafely",
        "team": "Tech shared",
    },
    "ehrql": {
        "org": "opensafely-core",
        "team": "Team RAP",
    },
    "job-runner": {
        "org": "opensafely-core",
        "team": "Team RAP",
    },
    "job-server": {
        "org": "opensafely-core",
        "team": "Team REX",
    },
    "kissh": {
        "org": "ebmdatalab",
        "team": "Team RAP",
    },
    "metrics": {
        "org": "ebmdatalab",
        "team": "Team REX",
    },
    "openprescribing": {
        "org": "ebmdatalab",
        "team": "Team RAP",
    },
    "opensafely-cli": {
        "org": "opensafely-core",
        "team": "Team REX",
    },
    "opensafely.org": {
        "org": "ebmdatalab",
        "team": "Team REX",
    },
    "opencodelists": {
        "org": "opensafely-core",
        "team": "Team REX",
    },
    "pipeline": {
        "org": "opensafely-core",
        "team": "Team RAP",
    },
    "python-docker": {
        "org": "opensafely-core",
        "team": "Team RAP",
    },
    "reports": {
        "org": "opensafely-core",
        "team": "Team REX",
    },
    "repo-template": {
        "org": "opensafely-core",
        "team": "Tech shared",
    },
    "sqlrunner": {
        "org": "opensafely-core",
        "team": "Team RAP",
    },
    "team-manual": {
        "org": "ebmdatalab",
        "team": "Team REX",
    },
}

SKIPPED_WORKFLOWS_ON_MAIN = {
    "opensafely/documentation": [
        65834242,  # [On workflow dispatch] Check docs with Vale
    ],
    "opensafely-core/airlock": [
        94122733,  # [Ignored on main, PR#277] Docs
    ],
    "opensafely-core/cohort-extractor": [
        13520184,  # [On workflow dispatch] Check Trino version on EMIS and in docker-compose.yml match
    ],
    "opensafely-core/job-runner": [
        26915901,  # [On workflow call] Add software bill of materials to release (reusable)
        26915902,  # [On workflow call] Scan with Grype (reusable)
        25002877,  # [On PR] Dependency review
        2393224,  # [On PR] Tests
    ],
    "opensafely-core/pipeline": [
        77090712,  # [Disabled] Pin pydantic
    ],
    "opensafely-core/python-docker": [
        6866192,  # [On PR] Run tests
        21967294,  # Dependabot auto-approve and enable auto-merge
    ],
    "opensafely-core/sqlrunner": [
        37329087,  # Auto merge Dependabot PRs
    ],
    "ebmdatalab/bennettbot": [
        32719413,  # Auto merge Dependabot PRs
    ],
}

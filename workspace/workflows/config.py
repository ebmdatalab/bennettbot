SHORTHANDS = {
    "os": "opensafely",
    "osc": "opensafely-core",
    "ebm": "ebmdatalab",
}

REPOS = {
    "opensafely": [
        "documentation",
    ],
    "opensafely-core": [
        "job-server",
        "job-runner",
        "ehrql",
        "airlock",
        "opencodelists",
        "pipeline",
        "opensafely-cli",
        "python-docker",
        "backend-server",
        "sqlrunner",
        "cohort-extractor",
        "actions-registry",
        "reports",
    ],
    "ebmdatalab": [
        "openprescribing",
        "bennett.ox.ac.uk",
        "opensafely.org",
        "team-manual",
        "metrics",
        "kissh",
    ],
}

SKIPPED_WORKFLOWS_ON_MAIN = {
    "opensafely-core/airlock": [94122733],
    "opensafely-core/job-runner": [26915902, 25002877, 26915901],
    "opensafely-core/pipeline": [21951759],
    "opensafely-core/python-docker": [21967294],
    "opensafely-core/sqlrunner": [37329087],
    "opensafely-core/cohort-extractor": [13520184],
}

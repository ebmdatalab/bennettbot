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
        "bennettbot",
        "kissh",
    ],
}

SKIPPED_WORKFLOWS_ON_MAIN = {
    "opensafely/documentation": [
        65834242,  # [On workflow dispatch] Check docs with Vale
    ],
    "opensafely-core/airlock": [
        94122733,  # [Ignored on main, PR#277] Docs
    ],
    "opensafely-core/job-runner": [
        26915901,  # [On workflow call] Add software bill of materials to release (reusable)
        26915902,  # [On workflow call] Scan with Grype (reusable)
        25002877,  # [On PR] Dependency review
        2393224,  #  [On PR] Tests, TODO: Remove this after Simon's merge
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
    "opensafely-core/cohort-extractor": [
        13520184,  # [On workflow dispatch] Check Trino version on EMIS and in docker-compose.yml match
    ],
    "ebmdatalab/bennettbot": [
        32719413,  #  Auto merge Dependabot PRs
    ],
}

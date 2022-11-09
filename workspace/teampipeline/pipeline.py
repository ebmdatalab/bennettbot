from workspace import generate_report


def report():
    project_num = 12
    statuses = ["In Progress", "In Review", "Blocked"]
    return generate_report.main(project_num, statuses)

from workspace import generate_report


def report():
    project_num = 12
    statuses = ["In Progress", "Blocked"]
    generate_report.main(project_num, statuses)

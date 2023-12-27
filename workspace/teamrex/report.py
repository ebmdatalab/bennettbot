from workspace import generate_report


def report():
    project_num = 14
    statuses = ["In Progress", "In Review"]
    return generate_report.main(project_num, statuses)

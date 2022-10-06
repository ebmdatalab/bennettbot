from workspace import generate_report


def report():
    project_num = 13
    statuses = ["Under Review", "Blocked", "In Progress"]
    return generate_report.main(project_num, statuses)

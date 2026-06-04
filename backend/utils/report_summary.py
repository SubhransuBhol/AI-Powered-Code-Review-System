def calculate_summary(report_text):

    files_reviewed = report_text.count(
        "# File Review:"
    )

    bugs = 0
    security = 0
    improvements = 0

    current_section = None

    for line in report_text.splitlines():

        line = line.strip()

        if line.startswith("## Bugs"):
            current_section = "bugs"

        elif line.startswith("## Security Issues"):
            current_section = "security"

        elif line.startswith("## Improvements"):
            current_section = "improvements"

        elif line.startswith("*"):

            content = line[1:].strip()

            if content.lower() == "none":
                continue

            if current_section == "bugs":
                bugs += 1

            elif current_section == "security":
                security += 1

            elif current_section == "improvements":
                improvements += 1

    return {
        "files_reviewed": files_reviewed,
        "bugs": bugs,
        "security": security,
        "improvements": improvements
    }

def calculate_file_risk(review_text):

    summary = calculate_summary(review_text)

    bugs = summary["bugs"]
    security = summary["security"]

    if security >= 2:
        return "HIGH"

    elif security >= 1 or bugs >= 1:
        return "MEDIUM"

    return "LOW"

def calculate_overall_risk(file_risks):

    if "HIGH" in file_risks:
        return "HIGH"

    elif "MEDIUM" in file_risks:
        return "MEDIUM"

    return "LOW"
def get_severity(issue_text):

    text = issue_text.lower()

    if text.startswith("sql injection"):
        return "CRITICAL"

    if "parameterized queries" in text:
        return "MEDIUM"

    if "hardcoded password" in text:
        return "HIGH"

    if "password" in text:
        return "HIGH"

    if "authentication" in text:
        return "HIGH"

    if "jwt" in text:
        return "HIGH"

    if "token" in text:
        return "MEDIUM"

    if "input validation" in text:
        return "MEDIUM"

    if "error handling" in text:
        return "LOW"

    return "LOW"

def get_bandit_severity(finding):

    text = finding.lower()

    if "b608" in text:
        return "CRITICAL"

    if "b105" in text:
        return "HIGH"

    return "MEDIUM"

def add_severity_to_review(review):

    lines = []

    for line in review.splitlines():

        stripped = line.strip()

        if stripped.startswith("* "):

            issue = stripped[2:]

            severity = get_severity(
                issue
            )

            if issue.lower() != "none":

                line = (
                    f"* [{severity}] {issue}"
                )

        lines.append(line)

    return "\n".join(lines)
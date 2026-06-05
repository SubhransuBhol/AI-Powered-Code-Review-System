import os
from services.review_engine import review_single_file
from static_analysis.bandit_runner import (
    run_bandit
)
from utils.severity_mapper import (
    get_bandit_severity, add_severity_to_review
)
from utils.fix_generator import add_fixes_to_review


def review_file(file_data):

    filename = os.path.basename(
        file_data["filename"]
    )

    filepath = file_data.get("filepath")

    content = file_data["content"]

    if filepath:
        bandit_findings = run_bandit(
            filepath
        )
    else:
        bandit_findings = []
    
    review = review_single_file(
        filename,
        content
    )

    review = add_severity_to_review(review)
    
    if bandit_findings:
        review += "\n\n## Static Analysis Findings\n"
        for finding in bandit_findings:
            severity = get_bandit_severity(
                finding
            )
            review += (
                f"\n* [{severity}] {finding}"
            )

    review = add_fixes_to_review(review)

    return filename, review
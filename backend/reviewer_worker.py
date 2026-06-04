import os

from review_engine import review_single_file
from static_analysis.bandit_runner import (
    run_bandit
)


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
    if bandit_findings:

        review += "\n\n## Static Analysis Findings\n"

        for finding in bandit_findings:

            review += f"\n* {finding}"

    return filename, review
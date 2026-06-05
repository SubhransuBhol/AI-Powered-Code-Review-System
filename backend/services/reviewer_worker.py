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
    from utils.fix_generator import generate_secret_recommendations, check_config_security

    filename = os.path.basename(
        file_data["filename"]
    )
    relative_filename = file_data["filename"]
    filepath = file_data.get("filepath")
    content = file_data["content"]
    project_context = file_data.get("project_context")
    has_env_file = file_data.get("has_env_file", True)

    if filepath:
        bandit_findings = run_bandit(
            filepath
        )
    else:
        bandit_findings = []
    
    review = review_single_file(
        filename,
        content,
        project_context=project_context
    )

    review = add_severity_to_review(review)
    
    # Configuration Security Check Findings
    config_findings = check_config_security(relative_filename, content)
    if config_findings:
        findings_str = "\n".join([f"* [HIGH] {f}" for f in config_findings])
        if "## Security Issues" in review:
            review = review.replace("## Security Issues", f"## Security Issues\n{findings_str}")
        else:
            review += f"\n\n## Security Issues\n{findings_str}"
    
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

    # Secret Management Recommendations
    secret_rec = generate_secret_recommendations(relative_filename, content, has_env_file)
    if secret_rec:
        review += "\n\n" + secret_rec

    return filename, review
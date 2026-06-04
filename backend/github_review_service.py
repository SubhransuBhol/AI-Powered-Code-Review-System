from master_review import generate_master_review
from master_review_builder import (
    build_score,
    build_critical_issues,
    build_recommendations,
    parse_llm_sections,
    stitch_master_review
)
from utils.github_cloner import clone_repository
from rag.project_vectorizer import vectorize_project
from rag.hybrid_retriever import hybrid_retrieve
from review_engine import review_single_file
from utils.report_saver import save_report
from rag.review_query import generate_review_query
from rag.vector_store import clear_collection
from utils.file_reader import get_project_files
from utils.report_summary import (
    calculate_file_risk,calculate_overall_risk
)
from static_analysis.bandit_runner import (
    run_bandit
)
import time
import os

def parse_issues(review_text):
    bugs_count = 0
    security_count = 0
    current_section = None
    
    for line in review_text.splitlines():
        line_stripped = line.strip()
        if line_stripped.startswith("## Bugs"):
            current_section = "bugs"
        elif line_stripped.startswith("## Security Issues"):
            current_section = "security"
        elif line_stripped.startswith("# File Review:"):
            current_section = None
        elif line_stripped.startswith(("* ", "- ")):
            bullet_content = line_stripped[2:].strip().lower()
            if bullet_content != "none" and bullet_content != "...":
                if current_section == "bugs":
                    bugs_count += 1
                elif current_section == "security":
                    security_count += 1
    return bugs_count, security_count

def parse_single_review(review_text):
    bugs_count = 0
    security_count = 0
    improvements_count = 0
    findings = []
    seen_findings = set()
    current_section = None
    
    for line in review_text.splitlines():
        line_stripped = line.strip()
        if line_stripped.startswith("## Bugs"):
            current_section = "bugs"
        elif line_stripped.startswith("## Security Issues"):
            current_section = "security"
        elif line_stripped.startswith("## Improvements"):
            current_section = "improvements"
        elif line_stripped.startswith("# File Review:"):
            current_section = None
        elif line_stripped.startswith(("* ", "- ")):
            bullet_content = line_stripped[2:].strip()
            compare_content = bullet_content.lower()
            if compare_content not in ("none", "...", "none."):
                if current_section == "bugs":
                    bugs_count += 1
                    issue_key = bullet_content.split(":")[0].strip()
                    if issue_key not in seen_findings:
                        findings.append(bullet_content)
                        seen_findings.add(issue_key)
                elif current_section == "security":
                    security_count += 1
                    issue_key = bullet_content.split(":")[0].strip()
                    if issue_key not in seen_findings:
                        findings.append(bullet_content)
                        seen_findings.add(issue_key)
                elif current_section == "improvements":
                    improvements_count += 1
    return bugs_count, security_count, improvements_count, findings

def review_github_repository(
    repo_url
):
    total_start_time = time.time()

    print("Cloning Repository")

    clone_path = clone_repository(
        repo_url
    )

    print("Clearing Previous Vectors")

    clear_collection()

    print("Vectorizing Repository")

    vectorize_project(
        clone_path
    )

    files = get_project_files(
        clone_path
    )

    print(
        "Files Found:",
        len(files)
    )

    query = generate_review_query()

    print("Retrieving Relevant Files")

    hybrid_files = hybrid_retrieve(query, files, semantic_top_k=5)
    ids = [f["filename"] for f in hybrid_files]
    documents = [f["content"] for f in hybrid_files]
    filepaths = [f.get("filepath") for f in hybrid_files]
    
    print(
        "Retrieved Files:",
        ids
    )

    all_reviews = ""
    file_risks = []
    high_risk_files = []
    total_bugs = 0
    total_security = 0
    total_improvements = 0
    critical_findings = []

    for filename, filepath, content in zip(
        ids,
        filepaths,
        documents
    ):
        print(f"Reviewing: {filename}")

        review = review_single_file(filename, content)

        if filepath:
            bandit_findings = run_bandit(filepath)
        else:
            bandit_findings = []

        if bandit_findings:
            review += "\n\n## Static Analysis Findings\n"
            for finding in bandit_findings:
                review += f"\n* {finding}"

        risk = calculate_file_risk(review)
        file_risks.append(risk)
        if risk.upper() == "HIGH":
            high_risk_files.append(filename)

        bugs, sec, imps, findings = parse_single_review(review)
        total_bugs += bugs
        total_security += sec
        total_improvements += imps
        critical_findings.extend(findings)

        all_reviews += (
            f"\n\n# File Review: {filename}\n\n"
            f"## Risk Level\n"
            f"* {risk}\n\n"
            + review
            + "\n"
        )
    
    overall_risk = calculate_overall_risk(file_risks)

    print("Generating Presentation Report")
    master_total_start = time.time()

    score_sec = build_score(total_bugs, total_security, total_improvements)
    critical_sec = build_critical_issues(critical_findings)
    recs_sec = build_recommendations(total_bugs, total_security, total_improvements)
    
    py_sections = {
        "code_quality": score_sec,
        "critical_issues": critical_sec,
        "recommendations": recs_sec
    }

    high_risk_str = ""
    if high_risk_files:
        for hrf in high_risk_files:
            high_risk_str += f"\n* {hrf}"
    else:
        high_risk_str = "\n* None"

    critical_str = ""
    if critical_findings:
        for cf in critical_findings:
            critical_str += f"\n* {cf}"
    else:
        critical_str = "\n* None"

    master_review_input = f"""Files Reviewed: {len(ids)}
        Overall Risk: {overall_risk}
        Total Bugs: {total_bugs}
        Total Security Issues: {total_security}
        Total Improvements: {total_improvements}

        High Risk Files:{high_risk_str}

        Critical Findings:{critical_str}"""

    llm_output = generate_master_review(master_review_input)
    llm_sections = parse_llm_sections(llm_output)
    project_summary = stitch_master_review(llm_sections, py_sections)

    master_total_time = time.time() - master_total_start

    master_report = (
        "# PROJECT LEVEL ANALYSIS\n\n"
        + project_summary
        + "\n\n"
        + all_reviews.strip()
    )

    report_file = save_report(
        master_report,
        overall_risk
    )

    return {
        "report": all_reviews,
        "report_file": report_file["markdown"],
        "pdf_file": report_file["pdf"]
    }

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

    for filename,filepath, content in zip(
        ids,
        filepaths,
        documents
    ):

        print(
            f"Reviewing: {filename}"
        )

        review = review_single_file(
            filename,
            content
        )

        if filepath:
            bandit_findings = run_bandit(
                filepath
            )
        else:
            bandit_findings = []

        if bandit_findings:

            review += "\n\n## Static Analysis Findings\n"

            for finding in bandit_findings:

                review += f"\n* {finding}"

        risk = calculate_file_risk(review)

        file_risks.append(risk)

        all_reviews += (
            f"\n\n# File Review: {filename}\n\n"
            f"## Risk Level\n"
            f"* {risk}\n\n"
            + review
            + "\n"
        )
    
    overall_risk = calculate_overall_risk(
        file_risks
    )

    print("Generating Presentation Report")

    master_report = all_reviews.strip()

    report_file = save_report(
        master_report,
        overall_risk
    )

    return {
        "report": all_reviews,
        "report_file": report_file["markdown"],
        "pdf_file": report_file["pdf"]
    }

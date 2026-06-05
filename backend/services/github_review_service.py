from services.master_review import generate_master_review
from services.master_review_builder import (
    build_score,
    build_critical_issues,
    build_recommendations,
    parse_llm_sections,
    stitch_master_review
)
from utils.duplicate_detector import (
    detect_duplicates,
    generate_duplicate_report_section
)
from dependency_scanner.dependency_scanner import (
    scan_project_dependencies,
    generate_dependency_report_section
)
from utils.architecture_analyzer import (
    analyze_architecture,
    generate_architecture_report_section
)
from utils.github_cloner import clone_repository
from rag.project_vectorizer import vectorize_project
from rag.hybrid_retriever import hybrid_retrieve
from services.review_engine import review_single_file
from utils.report_saver import save_report
from rag.review_query import generate_review_query
from rag.vector_store import clear_collection
from utils.file_reader import get_project_files
from utils.report_summary import (
    calculate_file_risk,calculate_overall_risk
)
from utils.severity_mapper import (
    get_bandit_severity, add_severity_to_review
)
from utils.fix_generator import add_fixes_to_review
from static_analysis.bandit_runner import (
    run_bandit
)
from concurrent.futures import ThreadPoolExecutor
from services.reviewer_worker import review_file
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
    
    # Analyze architecture first to get project_type for context
    all_files_dict = {f["filename"]: f["content"] for f in files}
    arch_analysis = analyze_architecture(all_files_dict)
    project_type = arch_analysis.get("project_type", "Backend API Application")
    
    from utils.file_reader import build_lightweight_context
    selected_filenames = [f["filename"] for f in hybrid_files]
    project_context = build_lightweight_context(files, selected_filenames, project_type)
    
    has_env_file = any(f["filename"].endswith(".env") or ".env." in f["filename"] for f in files)
    file_path_map = {f["filename"]: f.get("filepath") for f in hybrid_files}
    
    print(
        "Retrieved Files:",
        ids
    )

    review_jobs = []
    for filename, content in zip(ids, documents):
        review_jobs.append({
            "filename": filename,
            "content": content,
            "filepath": file_path_map.get(filename),
            "project_context": project_context,
            "has_env_file": has_env_file
        })

    all_reviews = ""
    file_risks = []
    high_risk_files = []
    total_bugs = 0
    total_security = 0
    total_improvements = 0
    critical_findings = []

    MAX_WORKERS = min(
        max(2, (os.cpu_count() or 4) // 2),
        3
    )
    max_workers = min(
        len(review_jobs),
        MAX_WORKERS
    )

    print(f"Review Jobs: {len(review_jobs)}")
    print(f"Worker Threads: {max_workers}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(review_file, review_jobs)

        for filename, review in results:
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

    all_files_dict = {f["filename"]: f["content"] for f in files}
    duplicates = detect_duplicates(all_files_dict)
    dup_sec = generate_duplicate_report_section(duplicates)
    
    manifests_found, dep_findings = scan_project_dependencies(all_files_dict)
    dep_sec = generate_dependency_report_section(manifests_found, dep_findings)
    
    arch_analysis = analyze_architecture(all_files_dict)
    arch_sec = generate_architecture_report_section(arch_analysis)
    
    arch_risk = arch_analysis.get("risk_level")
    has_duplicates = bool(duplicates)
    
    score_sec = build_score(
        total_bugs,
        total_security,
        total_improvements,
        critical_findings=critical_findings,
        architecture_risk=arch_risk,
        has_duplicates=has_duplicates
    )
    critical_sec = build_critical_issues(critical_findings)
    recs_sec = build_recommendations(total_bugs, total_security, total_improvements)
    
    py_sections = {
        "code_quality": score_sec,
        "critical_issues": critical_sec,
        "recommendations": recs_sec,
        "dependency_security": dep_sec,
        "architecture_analysis": arch_sec,
        "duplicate_code": dup_sec
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

    from services.master_review_builder import validate_and_fix_consistency
    llm_sections = validate_and_fix_consistency(
        llm_sections,
        critical_findings=critical_findings,
        total_security=total_security,
        overall_risk=overall_risk,
        high_risk_files=high_risk_files,
        all_reviews_text=all_reviews,
        total_bugs=total_bugs,
        total_improvements=total_improvements
    )

    project_summary = stitch_master_review(llm_sections, py_sections)

    master_total_time = time.time() - master_total_start

    master_report = (
        "# PROJECT LEVEL ANALYSIS\n\n"
        + project_summary
        + "\n\n"
        + all_reviews.strip()
    )

    from services.master_review_builder import final_report_count_validator
    master_report = final_report_count_validator(
        master_report,
        total_improvements=total_improvements,
        total_bugs=total_bugs,
        total_security=total_security
    )

    report_file = save_report(
        master_report,
        overall_risk
    )

    return {
        "report": master_report,
        "report_file": report_file["markdown"],
        "pdf_file": report_file["pdf"]
    }

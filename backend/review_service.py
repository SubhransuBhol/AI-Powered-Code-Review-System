from rag.project_vectorizer import vectorize_project
from rag.hybrid_retriever import hybrid_retrieve
from rag.review_query import generate_review_query
from utils.zip_handler import extract_zip
from utils.file_reader import get_project_files
from rag.vector_store import clear_collection
from review_engine import review_single_file
from master_review import generate_master_review
from utils.report_saver import save_report
from utils.report_summary import (
    calculate_file_risk,calculate_overall_risk
)
from concurrent.futures import ThreadPoolExecutor
from reviewer_worker import review_file
import time
import os

def parse_issues(review_text):
    bugs_count = 0
    security_count = 0
    current_section = None
    improvement_count = 0
    
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
            bullet_content = line_stripped[2:].strip().lower()
            if bullet_content != "none" and bullet_content != "...":
                if current_section == "bugs":
                    bugs_count += 1
                elif current_section == "security":
                    security_count += 1
                elif current_section == "improvements":
                    improvement_count += 1
    return bugs_count, security_count, improvement_count

def review_project(zip_path):
    total_start_time = time.time()

    print("Step 1: Extracting ZIP")
    start = time.time()

    extract_path = "../uploads/extracted_project"
    extract_zip(zip_path, extract_path)

    print("Extraction:", time.time() - start)

    print("Step 2: Reading Files")
    start = time.time()

    files = get_project_files(extract_path)

    print("Files found:", len(files))
    print("Reading:", time.time() - start)

    print("Clearing Previous Vectors")

    clear_collection()

    print("Vectorizing Project")

    vectorize_project(
        extract_path
    )

    query = generate_review_query()

    print(f"Stored {len(files)} files")

    print("Retrieving Relevant Files")

    hybrid_files = hybrid_retrieve(query, files, semantic_top_k=5)
    filepaths = [f.get("filepath") for f in hybrid_files]
    ids = [os.path.basename(f["filename"]) for f in hybrid_files]
    documents = [f["content"] for f in hybrid_files]

    print(
        "Retrieved Files:",
        ids
    )
    file_risks = []

    all_reviews = ""

    review_jobs = []

    for filename, filepath, content in zip(
        ids,
        filepaths,
        documents
    ):

        review_jobs.append({
            "filename": filename,
            "filepath": filepath,
            "content": content
        })

    all_reviews = ""

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

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:

        results = executor.map(
            review_file,
            review_jobs
        )

        for filename, review in results:

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

    report_file = save_report(master_report,overall_risk)

    return {
        "report": master_report,
        "report_file": report_file["markdown"],
        "pdf_file": report_file["pdf"]
    }

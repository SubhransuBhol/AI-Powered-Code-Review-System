from datetime import datetime
from utils.pdf_generator import (
    generate_pdf_report
)
from utils.report_summary import (
    calculate_summary
)

def save_report(report):
    # Strip the Summary Dashboard from the report
    if "## Detailed File Reviews" in report:
        parts = report.split("## Detailed File Reviews", 1)
        report = parts[1].strip()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../reports/review_{timestamp}.md"

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(report)
    
    pdf_file = filename.replace(
        ".md",
        ".pdf"
    )

    summary = calculate_summary(report)

    generate_pdf_report(
        report,
        pdf_file,
        summary
    )

    return {
        "markdown": filename,
        "pdf": pdf_file,
    }
# No patching needed anymore

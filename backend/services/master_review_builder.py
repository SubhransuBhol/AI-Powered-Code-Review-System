def build_score(bugs, security, improvements):
    """
    Computes Code Quality Score out of 10 with a softer scoring model.
    """
    # Soft deduction rates with improvement penalty capped at 10 improvements (max -1.0 point)
    raw_score = 10.0 - (bugs * 0.5) - (security * 1.0) - (min(improvements, 10) * 0.1)
    
    # Bounded between 1 and 10, rounded to nearest integer
    score = max(1, min(10, int(round(raw_score))))
    
    if score >= 9:
        score_just = "Excellent code quality with clean architecture and no critical issues."
    elif score >= 7:
        score_just = "Good code quality, but minor bugs or refactoring needs attention."
    elif score >= 5:
        score_just = "Moderate code quality; some security concerns and bugs need attention."
    else:
        score_just = "Low code quality; critical vulnerabilities and bugs detected."
    
    return f"## Code Quality Score\n* {score}/10 ({score_just})"

def build_critical_issues(critical_findings):

    unique_findings = []
    seen = set()

    for finding in critical_findings:

        issue_key = finding.split(":")[0].strip()

        if issue_key not in seen:
            unique_findings.append(finding)
            seen.add(issue_key)

    critical_findings = unique_findings
    
    """
    Formats the critical issues section.
    """
    critical_findings = list(
        dict.fromkeys(
            critical_findings
        )
    )

    if critical_findings:
        items = []
        for finding in critical_findings[:3]:
            items.append(f"* {finding}")
        return "## Critical Issues\n" + "\n".join(items)
    else:
        return "## Critical Issues\n* None identified."

def build_recommendations(bugs, security, improvements):
    """
    Formats the recommended actions based on findings.
    """
    recs = []
    if security > 0:
        recs.append("Remediate security risks immediately by sanitizing database queries and using environment variables.")
    if bugs > 0:
        recs.append("Resolve functional bugs to ensure runtime stability and prevent unexpected exceptions.")
    if improvements > 0:
        recs.append("Apply suggested code refactoring and data validation improvements for better maintainability.")
    if not recs:
        recs.append("Perform regular review scans and continue following code quality best practices.")
    
    return "## Recommended Actions\n" + "\n".join([f"* {r}" for r in recs])

def parse_llm_sections(llm_output):
    """
    Parses LLM-generated output to extract Executive Assessment, Strengths, Weaknesses,
    Security Assessment, and Final Verdict.
    """
    sections = {
        "executive": "## Executive Assessment\n* Pending evaluation.",
        "strengths": "## Strengths\n* Pending analysis.",
        "weaknesses": "## Weaknesses\n* Pending analysis.",
        "security": "## Security Assessment\n* Pending security review.",
        "verdict": "## Final Verdict\n* Pending final decision."
    }
    
    current_key = None
    current_lines = []
    
    for line in llm_output.splitlines():
        line_stripped = line.strip()
        if "Executive Assessment" in line_stripped:
            if current_key and current_lines:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = "executive"
            current_lines = [line]
        elif "Strengths" in line_stripped:
            if current_key and current_lines:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = "strengths"
            current_lines = [line]
        elif "Weaknesses" in line_stripped:
            if current_key and current_lines:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = "weaknesses"
            current_lines = [line]
        elif "Security Assessment" in line_stripped:
            if current_key and current_lines:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = "security"
            current_lines = [line]
        elif "Final Verdict" in line_stripped:
            if current_key and current_lines:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = "verdict"
            current_lines = [line]
        else:
            if current_key:
                current_lines.append(line)
                
    if current_key and current_lines:
        sections[current_key] = "\n".join(current_lines).strip()
        
    return sections

def stitch_master_review(llm_sections, py_sections):
    """
    Combines Qwen-generated sections with Python rule-based sections in the exact requested order.
    """
    parts = [
        llm_sections["executive"],
        py_sections["code_quality"],
        llm_sections["strengths"],
        llm_sections["weaknesses"],
        py_sections["critical_issues"],
        llm_sections["security"],
        py_sections["recommendations"],
        py_sections.get("dependency_security"),
        py_sections.get("architecture_analysis"),
        py_sections["duplicate_code"],
        llm_sections["verdict"]
    ]
    parts = [p for p in parts if p]
    return "\n\n".join(parts)


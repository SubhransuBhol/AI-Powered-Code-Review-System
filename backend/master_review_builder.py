def build_python_sections(summary_dict):
    """
    Computes Code Quality Score, Strengths, Weaknesses, Critical Issues, and Recommended Actions
    using Python rule-based logic.
    """
    total_bugs = summary_dict.get("bugs", 0)
    total_security = summary_dict.get("security", 0)
    total_improvements = summary_dict.get("improvements", 0)
    high_risk_files = summary_dict.get("high_risk_files", [])
    critical_findings = summary_dict.get("critical_findings", [])
    
    # 1. Code Quality Score
    score = max(1, 10 - (total_bugs * 2) - (total_security * 3) - int(total_improvements * 0.2))
    score = min(10, score)
    if score >= 9:
        score_just = "Excellent code quality with clean architecture and no critical issues."
    elif score >= 7:
        score_just = "Good code quality, but minor bugs or refactoring needs attention."
    elif score >= 5:
        score_just = "Moderate code quality; some security concerns and bugs need attention."
    else:
        score_just = "Low code quality; critical vulnerabilities and bugs detected."
    
    code_quality_str = f"## Code Quality Score\n* {score}/10 ({score_just})"
    
    # 2. Strengths
    strengths = []
    if total_bugs == 0:
        strengths.append("Robust implementation: Zero critical bugs identified in core files.")
    else:
        strengths.append("Modular structure: Codebase layout is well-organized and modular.")
    if total_security == 0:
        strengths.append("Strong security baseline: No severe security concerns or vulnerability patterns found.")
    else:
        strengths.append("Defined endpoints: Functional boundaries are clear and structured.")
    
    strengths_str = "## Strengths\n" + "\n".join([f"* {s}" for s in strengths])
    
    # 3. Weaknesses
    weaknesses = []
    if total_bugs > 0:
        weaknesses.append(f"Quality issues: {total_bugs} functional bugs detected.")
    if total_security > 0:
        weaknesses.append(f"Security exposure: {total_security} potential security vulnerabilities found.")
    if total_improvements > 0:
        weaknesses.append(f"Refactoring opportunities: {total_improvements} code style/structure improvements suggested.")
    if not weaknesses:
        weaknesses.append("No major code quality weaknesses were identified.")
        
    weaknesses_str = "## Weaknesses\n" + "\n".join([f"* {w}" for w in weaknesses])
    
    # 4. Critical Issues
    critical_issues = []
    if critical_findings:
        critical_issues = critical_findings[:3]
    else:
        critical_issues = ["None identified."]
        
    critical_str = "## Critical Issues\n" + "\n".join([f"* {c}" for c in critical_issues])
    
    # 5. Recommended Actions
    recs = []
    if total_security > 0:
        recs.append("Remediate security risks immediately by sanitizing database queries and using environment variables.")
    if total_bugs > 0:
        recs.append("Resolve functional bugs to ensure runtime stability and prevent unexpected exceptions.")
    if total_improvements > 0:
        recs.append("Apply suggested code refactoring and data validation improvements for better maintainability.")
    if not recs:
        recs.append("Perform regular review scans and continue following code quality best practices.")
        
    recs_str = "## Recommended Actions\n" + "\n".join([f"* {r}" for r in recs])
    
    return {
        "code_quality": code_quality_str,
        "strengths": strengths_str,
        "weaknesses": weaknesses_str,
        "critical_issues": critical_str,
        "recommendations": recs_str
    }

def parse_llm_sections(llm_output):
    """
    Parses LLM-generated output to extract Executive Assessment, Security Assessment, and Final Verdict.
    """
    sections = {
        "executive": "## Executive Assessment\n* Pending evaluation.",
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

def stitch_summary(llm_sections, py_sections):
    """
    Combines Qwen-generated sections with Python rule-based sections in the exact requested order.
    """
    parts = [
        llm_sections["executive"],
        py_sections["code_quality"],
        py_sections["strengths"],
        py_sections["weaknesses"],
        py_sections["critical_issues"],
        llm_sections["security"],
        py_sections["recommendations"],
        llm_sections["verdict"]
    ]
    return "\n\n".join(parts)

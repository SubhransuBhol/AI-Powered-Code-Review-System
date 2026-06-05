def build_score(bugs, security, improvements, critical_findings=None, architecture_risk=None, has_duplicates=False):
    """
    Computes Code Quality Score out of 10 with balanced calibrated scoring model.
    """
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    
    if critical_findings:
        for finding in critical_findings:
            finding_upper = finding.upper()
            if "[CRITICAL]" in finding_upper:
                critical_count += 1
            elif "[HIGH]" in finding_upper:
                high_count += 1
            elif "[MEDIUM]" in finding_upper:
                medium_count += 1
            elif "[LOW]" in finding_upper:
                low_count += 1
            else:
                low_count += 1
                
    low_count += improvements
    
    # Apply balanced deductions with caps
    critical_deduction = min(3.0, critical_count * 1.5)
    high_deduction = min(2.0, high_count * 1.0)
    medium_deduction = min(1.5, medium_count * 0.5)
    low_deduction = min(1.0, low_count * 0.1)
    
    deduction = critical_deduction + high_deduction + medium_deduction + low_deduction
    
    # Consider architecture risk and duplicates
    if architecture_risk:
        if architecture_risk.upper() == "HIGH":
            deduction += 1.0
        elif architecture_risk.upper() == "MEDIUM":
            deduction += 0.5
            
    if has_duplicates:
        deduction += 0.5
        
    score = 10.0 - deduction
    score = max(1.0, score)
    final_score = int(round(score))
    
    if final_score >= 9:
        score_just = "Excellent code quality with clean architecture and no critical issues."
    elif final_score >= 7:
        score_just = "Good code quality, but minor bugs or refactoring needs attention."
    elif final_score >= 5:
        score_just = "Moderate code quality; some security concerns and bugs need attention."
    else:
        score_just = "Low code quality; critical vulnerabilities and bugs detected."
    
    return f"## Code Quality Score\n* {final_score}/10 ({score_just})"

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

def validate_and_fix_consistency(llm_sections, critical_findings, total_security, overall_risk, high_risk_files, all_reviews_text, total_bugs=0, total_improvements=0):
    import re
    has_critical = len(critical_findings) > 0 or overall_risk.upper() in ("HIGH", "MEDIUM") or len(high_risk_files) > 0
    
    keywords = ["sql injection", "hardcoded credentials", "hardcoded password", "hardcoded secret", "critical security", "critical vulnerability"]
    reviews_lower = all_reviews_text.lower()
    has_critical_indicators = has_critical or any(kw in reviews_lower for kw in keywords)
    
    if has_critical_indicators:
        forbidden_phrases = [
            (re.compile(r'\bsafe repository\b', re.IGNORECASE), "repository requiring security hardening"),
            (re.compile(r'\brobust security\b', re.IGNORECASE), "security posture requiring remediation"),
            (re.compile(r'\bsecure design\b', re.IGNORECASE), "design needing security remediation"),
            (re.compile(r'\bno high-risk files\b', re.IGNORECASE), "critical risk files identified"),
            (re.compile(r'\bproduction ready\b', re.IGNORECASE), "not production ready due to outstanding security findings")
        ]
        
        for key in ["executive", "security", "verdict"]:
            if key not in llm_sections:
                continue
            text = llm_sections[key]
            for pattern, repl in forbidden_phrases:
                text = pattern.sub(repl, text)
            llm_sections[key] = text
            
    # Sync bug, security and improvement counts across LLM sections
    for key in llm_sections.keys():
        if key not in llm_sections:
            continue
        text = llm_sections[key]
        
        text = qualitative_replace_narrative(text, total_improvements, total_bugs, total_security)
        
        llm_sections[key] = text
        
    return llm_sections

def qualitative_replace_narrative(text, total_improvements, total_bugs, total_security):
    import re
    
    # Robust count-normalization layer
    opt_words = r'(?:total|identified|detected|reported|found|suggested)'
    opt_words_pl = r'(?:total|identified|detected|reported|found|suggested|were|was|are|is|in\s+total)'
    opt_link = r'(?:is|are|was|were|total|suggested|identified|detected|reported|found|:|\s)'
    
    # 1. Improvements
    pattern_improvements_pre = re.compile(
        r'\b\d+\s+'
        r'(?:' + opt_words + r'\s+)?'
        r'improvements?\b(?!\s+(?:suggestions?|areas|findings|for))'
        r'(?:\s+' + opt_words_pl + r')?\b',
        re.IGNORECASE
    )
    pattern_improvements_suf = re.compile(
        r'\bimprovements?\s*' + opt_link + r'*\s*\d+\b',
        re.IGNORECASE
    )
    if total_improvements > 0:
        text = pattern_improvements_pre.sub("several improvements identified", text)
        text = pattern_improvements_suf.sub("several improvements identified", text)
    else:
        text = pattern_improvements_pre.sub("no improvements suggested", text)
        text = pattern_improvements_suf.sub("no improvements suggested", text)
        
    # 2. Bugs
    pattern_bugs_pre = re.compile(
        r'\b\d+\s+'
        r'(?:' + opt_words + r'\s+)?'
        r'bugs?'
        r'(?:\s+' + opt_words_pl + r')?\b',
        re.IGNORECASE
    )
    pattern_bugs_suf = re.compile(
        r'\bbugs?\s*' + opt_link + r'*\s*\d+\b',
        re.IGNORECASE
    )
    if total_bugs > 0:
        text = pattern_bugs_pre.sub("functional issues identified", text)
        text = pattern_bugs_suf.sub("functional issues identified", text)
    else:
        text = pattern_bugs_pre.sub("no functional bugs", text)
        text = pattern_bugs_suf.sub("no functional bugs", text)
        
    # 3. Security issues / Vulnerabilities
    pattern_security_pre = re.compile(
        r'\b\d+\s+'
        r'(?:' + opt_words + r'\s+)?'
        r'(?:security\s+issues?|vulnerabilit(?:y|ies))'
        r'(?:\s+' + opt_words_pl + r')?\b',
        re.IGNORECASE
    )
    pattern_security_suf = re.compile(
        r'\b(?:security\s+issues?|vulnerabilit(?:y|ies))\s*' + opt_link + r'*\s*\d+\b',
        re.IGNORECASE
    )
    if total_security > 0:
        text = pattern_security_pre.sub("multiple security concerns detected", text)
        text = pattern_security_suf.sub("multiple security concerns detected", text)
    else:
        text = pattern_security_pre.sub("no security concerns", text)
        text = pattern_security_suf.sub("no security concerns", text)
        
    # 4. Recommendations
    pattern_recommendations_pre = re.compile(
        r'\b\d+\s+'
        r'(?:' + opt_words + r'\s+)?'
        r'recommendations?'
        r'(?:\s+' + opt_words_pl + r')?\b',
        re.IGNORECASE
    )
    pattern_recommendations_suf = re.compile(
        r'\brecommendations?\s*' + opt_link + r'*\s*\d+\b',
        re.IGNORECASE
    )
    if total_improvements > 0:
        text = pattern_recommendations_pre.sub("recommendations were provided", text)
        text = pattern_recommendations_suf.sub("recommendations were provided", text)
    else:
        text = pattern_recommendations_pre.sub("no recommendations", text)
        text = pattern_recommendations_suf.sub("no recommendations", text)
        
    # 5. Suggestions
    pattern_suggestions_pre = re.compile(
        r'\b\d+\s+'
        r'(?:' + opt_words + r'\s+)?'
        r'(?<!\brefactoring\s)(?<!\bimprovement\s)suggestions?'
        r'(?:\s+' + opt_words_pl + r')?\b',
        re.IGNORECASE
    )
    pattern_suggestions_suf = re.compile(
        r'\bsuggestions?\s*' + opt_link + r'*\s*\d+\b',
        re.IGNORECASE
    )
    if total_improvements > 0:
        text = pattern_suggestions_pre.sub("suggestions were provided", text)
        text = pattern_suggestions_suf.sub("suggestions were provided", text)
    else:
        text = pattern_suggestions_pre.sub("no suggestions", text)
        text = pattern_suggestions_suf.sub("no suggestions", text)

    # Fallback/specific qualitative replacements for improvements
    if total_improvements > 0:
        text = re.sub(r'\b\d+\s+suggested\s+improvements?\b', "several suggested improvements", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+improvements?\s+suggested\b', "several improvements suggested", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+improvement\s+suggestions?\b', "improvement suggestions", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+suggestions?\s+for\s+improvements?\b', "suggestions for improvement", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+areas\s+of\s+improvements?\b', "improvement opportunities exist across the codebase", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+refactoring\s+suggestions?\b', "refactoring suggestions", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+improvements?\b(?!\s+(?:suggested|suggestions?|areas|findings|for))', "several improvements", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+suggestions?\b(?!\s+(?:for|suggested|improvements?))', "suggestions", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+recommendations?\b', "recommendations", text, flags=re.IGNORECASE)
        text = re.sub(r'\bimprovements?\s*(?::|is|are)?\s*\d+\b', "improvement opportunities exist across the codebase", text, flags=re.IGNORECASE)
        text = re.sub(r'\bTotal Improvements Suggested\s*(?::|is|are)?\s*\d+\b', "several improvements identified", text, flags=re.IGNORECASE)
        text = re.sub(r'\bTotal Improvements\s*(?::|is|are)?\s*\d+\b', "several improvements identified", text, flags=re.IGNORECASE)
    else:
        text = re.sub(r'\b\d+\s+suggested\s+improvements?\b', "no suggested improvements", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+improvements?\s+suggested\b', "no improvements suggested", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+improvement\s+suggestions?\b', "no improvement suggestions", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+suggestions?\s+for\s+improvements?\b', "no suggestions for improvement", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+areas\s+of\s+improvements?\b', "no areas of improvement identified", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+refactoring\s+suggestions?\b', "no refactoring suggestions", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+improvements?\b(?!\s+(?:suggested|suggestions?|areas|findings|for))', "no improvements", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+suggestions?\b(?!\s+(?:for|suggested|improvements?))', "no suggestions", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+recommendations?\b', "no recommendations", text, flags=re.IGNORECASE)
        text = re.sub(r'\bimprovements?\s*(?::|is|are)?\s*\d+\b', "no improvements identified", text, flags=re.IGNORECASE)
        text = re.sub(r'\bTotal Improvements Suggested\s*(?::|is|are)?\s*\d+\b', "no improvements identified", text, flags=re.IGNORECASE)
        text = re.sub(r'\bTotal Improvements\s*(?::|is|are)?\s*\d+\b', "no improvements identified", text, flags=re.IGNORECASE)

    # Fallback/specific qualitative replacements for bugs
    if total_bugs > 0:
        text = re.sub(r'\b\d+\s+suggested\s+bugs?\b', "functional bugs", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+bugs?\s+suggested\b', "functional bugs", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+functional\s+bugs?\b', "functional bugs", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+bugs?\b', "functional bugs", text, flags=re.IGNORECASE)
        text = re.sub(r'\bbugs?\s*(?::|is|are)?\s*\d+\b', "bug concerns", text, flags=re.IGNORECASE)
    else:
        text = re.sub(r'\b\d+\s+suggested\s+bugs?\b', "no suggested bugs", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+bugs?\s+suggested\b', "no bugs suggested", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+functional\s+bugs?\b', "no functional bugs", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+bugs?\b', "no bugs", text, flags=re.IGNORECASE)
        text = re.sub(r'\bbugs?\s*(?::|is|are)?\s*\d+\b', "no bug concerns", text, flags=re.IGNORECASE)

    # Fallback/specific qualitative replacements for security
    if total_security > 0:
        text = re.sub(r'\b\d+\s+suggested\s+security\s+issues?\b', "security issues", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+security\s+issues?\s+suggested\b', "security issues suggested", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+security\s+issues?\b', "security concerns were identified", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+security\s+findings\b', "security concerns", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+vulnerabilities\b', "security vulnerabilities", text, flags=re.IGNORECASE)
        text = re.sub(r'\bsecurity\s+issues?\s*(?::|is|are)?\s*\d+\b', "security concerns were identified", text, flags=re.IGNORECASE)
        text = re.sub(r'\bvulnerabilities\s*(?::|is|are)?\s*\d+\b', "security concerns were identified", text, flags=re.IGNORECASE)
    else:
        text = re.sub(r'\b\d+\s+suggested\s+security\s+issues?\b', "no suggested security issues", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+security\s+issues?\s+suggested\b', "no security issues suggested", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+security\s+issues?\b', "no security concerns", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+security\s+findings\b', "no security findings", text, flags=re.IGNORECASE)
        text = re.sub(r'\b\d+\s+vulnerabilities\b', "no vulnerabilities", text, flags=re.IGNORECASE)
        text = re.sub(r'\bsecurity\s+issues?\s*(?::|is|are)?\s*\d+\b', "no security concerns", text, flags=re.IGNORECASE)
        text = re.sub(r'\bvulnerabilities\s*(?::|is|are)?\s*\d+\b', "no security concerns", text, flags=re.IGNORECASE)

    # ==========================================
    # FINAL NARRATIVE CLEANUP
    # ==========================================

    # Improvement counts
    text = re.sub(
        r'\b\d+\s+areas\s+for\s+improvements?\b',
        'several improvement opportunities',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'\b\d+\s+areas\s+of\s+improvements?\b',
        'several improvement opportunities',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'\bcontains\s+\d+\s+areas\s+for\s+improvements?\b',
        'contains several improvement opportunities',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'\bthere\s+(?:are|were)\s+\d+\s+areas\s+for\s+improvements?\b',
        'several improvement opportunities were identified',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'\b\d+\s+improvement\s+opportunities\b',
        'several improvement opportunities',
        text,
        flags=re.IGNORECASE
    )

    # Bug counts
    text = re.sub(
        r'\bone\s+critical\s+bug\s+identified\b',
        'functional issues were identified',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'\b\d+\s+critical\s+bugs?\s+identified\b',
        'functional issues were identified',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'\bone\s+bug\s+identified\b',
        'functional issues were identified',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'\b\d+\s+bugs?\s+identified\b',
        'functional issues were identified',
        text,
        flags=re.IGNORECASE
    )

    # Security counts
    text = re.sub(
        r'\b\d+\s+security\s+issues?\b',
        'security concerns were identified',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'\b\d+\s+vulnerabilities\b',
        'security concerns were identified',
        text,
        flags=re.IGNORECASE
    )

    # Generic numeric narrative cleanup
    text = re.sub(
        r'\b\d+\s+areas\s+for\s+enhancement\b',
        'several enhancement opportunities',
        text,
        flags=re.IGNORECASE
    )
    return text

def final_report_count_validator(report_content, total_improvements, total_bugs=0, total_security=0):
    import re
    text = report_content
    
    def replace_section(match):
        header = match.group(1)
        content = match.group(2)
        cleaned_content = qualitative_replace_narrative(content, total_improvements, total_bugs, total_security)
        return header + cleaned_content

    # Target LLM narrative sections to replace numeric references with qualitative text
    pattern = re.compile(
        r'(## (?:Executive Assessment|Strengths|Weaknesses|Security Assessment|Final Verdict)\n)(.*?)(?=\n##|\n#|$)',
        re.DOTALL | re.IGNORECASE
    )
    text = pattern.sub(replace_section, text)
    
    return text


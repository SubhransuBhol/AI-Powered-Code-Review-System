from langchain_ollama import OllamaLLM
import hashlib
import time
import threading
import json
from collections import OrderedDict

# Thread-safe LRU Cache implementation
class ThreadSafeLRUCache:
    def __init__(self, capacity=100):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.lock = threading.Lock()

    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def clear(self):
        with self.lock:
            self.cache.clear()

# Dedicated chat model instance with a 384 token limit to allow up to 250 words
chat_llm = OllamaLLM(
    model="qwen2.5-coder:7b",
    temperature=0.0,
    options={
        "num_predict": 384,
        "temperature": 0.0
    }
)

chat_cache = ThreadSafeLRUCache(capacity=100)

def get_context_hash(review_context):
    try:
        serialized = json.dumps(review_context, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    except Exception:
        return hashlib.sha256(str(review_context).encode("utf-8")).hexdigest()

def split_report_by_headings(report):
    sections = {}
    current_heading = "intro"
    current_lines = []
    
    for line in report.splitlines():
        if line.startswith("# ") or line.startswith("## "):
            if current_lines:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = line.strip()
            current_lines = [line]
        else:
            current_lines.append(line)
            
    if current_lines:
        sections[current_heading] = "\n".join(current_lines).strip()
        
    return sections

def get_markdown_section_content(text, heading_keywords):
    if not text:
        return ""
    lines = text.splitlines()
    current_section_lines = []
    capture = False
    
    for line in lines:
        if line.startswith("# ") or line.startswith("## ") or line.startswith("### "):
            heading_clean = line.replace("#", "").strip().lower()
            if any(k.lower() in heading_clean for k in heading_keywords):
                capture = True
                current_section_lines.append(line)
            else:
                if capture:
                    break
        elif capture:
            current_section_lines.append(line)
            
    return "\n".join(current_section_lines).strip()

# ==========================================
# STRUCTURED REVIEW CONTEXT BUILDER
# ==========================================

def build_review_context(report_text):
    if not report_text:
        return {
            "master_review": "",
            "file_reviews": {},
            "architecture_analysis": "",
            "dependency_analysis": "",
            "duplicate_analysis": ""
        }
        
    parts = report_text.split("# File Review:")
    project_level_part = parts[0]
    file_review_parts = parts[1:]
    
    sections = split_report_by_headings(project_level_part)
    
    file_reviews = {}
    master_sections = {}
    architecture_analysis = ""
    dependency_analysis = ""
    duplicate_analysis = ""
    
    for heading, content in sections.items():
        heading_lower = heading.lower()
        if "repository architecture" in heading_lower:
            architecture_analysis = content
        elif "dependency security" in heading_lower:
            dependency_analysis = content
        elif "duplicate code" in heading_lower:
            duplicate_analysis = content
        else:
            master_sections[heading] = content
            
    master_review = "\n\n".join(master_sections.values())
    
    for part in file_review_parts:
        lines = part.splitlines()
        if not lines:
            continue
        filename = lines[0].strip()
        content = "\n".join(lines[1:]).strip()
        file_reviews[filename] = f"# File Review: {filename}\n{content}"
        
    return {
        "master_review": master_review,
        "file_reviews": file_reviews,
        "architecture_analysis": architecture_analysis,
        "dependency_analysis": dependency_analysis,
        "duplicate_analysis": duplicate_analysis
    }

# ==========================================
# BUTTON-SPECIFIC CONTEXT EXTRACTORS
# ==========================================

def get_critical_issues_context(review_context):
    master_crit = get_markdown_section_content(review_context.get("master_review", ""), ["critical issues"])
    
    master_issues = []
    if master_crit:
        for line in master_crit.splitlines():
            line_clean = line.strip()
            if (line_clean.startswith("*") or line_clean.startswith("-")) and "none" not in line_clean.lower():
                master_issues.append(line_clean)
                
    file_highs = []
    file_reviews = review_context.get("file_reviews", {})
    for filename, review_text in file_reviews.items():
        for line in review_text.splitlines():
            line_lower = line.lower()
            if any(w in line_lower for w in ["[high]", "[critical]"]):
                file_highs.append(f"* {line.strip().lstrip('*- ').strip()} (in {filename})")
                
    context = ""
    if master_issues:
        context += "## Critical Issues\n" + "\n".join(master_issues) + "\n\n"
    if file_highs:
        context += "## High/Critical Severity File Findings\n" + "\n".join(file_highs)
        
    return context.strip() or "The review did not identify any critical issues requiring immediate remediation."

def get_fix_prioritization_context(review_context):
    issues = {
        "CRITICAL": {"security": [], "bug": [], "improvement": []},
        "HIGH": {"security": [], "bug": [], "improvement": []},
        "MEDIUM": {"security": [], "bug": [], "improvement": []},
        "LOW": {"security": [], "bug": [], "improvement": []}
    }
    
    master_crit = get_markdown_section_content(review_context.get("master_review", ""), ["critical issues"])
    if master_crit:
        for line in master_crit.splitlines():
            line_clean = line.strip()
            if (line_clean.startswith("*") or line_clean.startswith("-")) and "none" not in line_clean.lower():
                text = line_clean.lstrip("*- ").strip()
                sev = "HIGH"
                if "[critical]" in text.lower():
                    sev = "CRITICAL"
                elif "[high]" in text.lower():
                    sev = "HIGH"
                elif "[medium]" in text.lower():
                    sev = "MEDIUM"
                elif "[low]" in text.lower():
                    sev = "LOW"
                
                for prefix in ["[critical]", "[high]", "[medium]", "[low]"]:
                    if text.lower().startswith(prefix):
                        text = text[len(prefix):].strip()
                        break
                        
                cat = "bug"
                if any(w in text.lower() for w in ["password", "token", "secret", "security", "vuln", "sql", "xss", "csrf", "inject", "auth", "encrypt"]):
                    cat = "security"
                elif any(w in text.lower() for w in ["improve", "refactor", "clean"]):
                    cat = "improvement"
                    
                issues[sev][cat].append(text)
                
    file_reviews = review_context.get("file_reviews", {})
    for filename, review_text in file_reviews.items():
        lines = review_text.splitlines()
        current_sec = None
        for line in lines:
            line_clean = line.strip()
            if "## bugs" in line_clean.lower():
                current_sec = "bug"
                continue
            elif "## security issues" in line_clean.lower():
                current_sec = "security"
                continue
            elif "## improvements" in line_clean.lower():
                current_sec = "improvement"
                continue
            elif line_clean.startswith("#") or line_clean.startswith("##"):
                current_sec = None
                continue
                
            if current_sec and (line_clean.startswith("*") or line_clean.startswith("-")):
                text = line_clean.lstrip("*- ").strip()
                if "none" in text.lower() or text == "":
                    continue
                
                sev = "LOW"
                if "[critical]" in text.lower():
                    sev = "CRITICAL"
                elif "[high]" in text.lower():
                    sev = "HIGH"
                elif "[medium]" in text.lower():
                    sev = "MEDIUM"
                elif "[low]" in text.lower():
                    sev = "LOW"
                else:
                    if current_sec == "security":
                        sev = "HIGH"
                    elif current_sec == "bug":
                        sev = "MEDIUM"
                        
                for prefix in ["[critical]", "[high]", "[medium]", "[low]"]:
                    if text.lower().startswith(prefix):
                        text = text[len(prefix):].strip()
                        break
                        
                full_text = f"{text} (in {filename})"
                if full_text not in issues[sev][current_sec]:
                    issues[sev][current_sec].append(full_text)
                    
    context = "## Prioritized Findings List\n\n"
    has_items = False
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    categories = ["security", "bug", "improvement"]
    
    for sev in severities:
        for cat in categories:
            for item in issues[sev][cat]:
                context += f"* **[{sev}]** ({cat.capitalize()}): {item}\n"
                has_items = True
                
    if not has_items:
        return "No high-priority fixes were identified. Focus can remain on general maintainability and code quality improvements."
            
    return context.strip()

def get_security_risks_context(review_context):
    master_sec = get_markdown_section_content(review_context.get("master_review", ""), ["security assessment"])
    master_crit = get_markdown_section_content(review_context.get("master_review", ""), ["critical issues"])
    
    has_sec_assess = False
    if master_sec:
        sec_clean = master_sec.replace("## Security Assessment", "").strip().lower()
        if sec_clean and "none identified" not in sec_clean and "none found" not in sec_clean and sec_clean != "none":
            has_sec_assess = True
            
    master_crit_issues = []
    if master_crit:
        for line in master_crit.splitlines():
            line_clean = line.strip()
            if (line_clean.startswith("*") or line_clean.startswith("-")) and "none" not in line_clean.lower():
                if any(w in line_clean.lower() for w in ["password", "token", "secret", "security", "vuln", "sql", "xss", "csrf", "inject", "auth", "encrypt"]):
                    master_crit_issues.append(line_clean)
                    
    file_sec_issues = []
    file_reviews = review_context.get("file_reviews", {})
    for filename, review_text in file_reviews.items():
        sec_sec = get_markdown_section_content(review_text, ["security issues"])
        if sec_sec:
            for line in sec_sec.splitlines():
                line_clean = line.strip()
                if (line_clean.startswith("*") or line_clean.startswith("-")) and "none" not in line_clean.lower():
                    file_sec_issues.append(f"* {line_clean.lstrip('*- ').strip()} (in {filename})")
                    
    context = ""
    if has_sec_assess:
        context += f"{master_sec}\n\n"
    if master_crit_issues:
        context += "## Critical Security Issues\n" + "\n".join(master_crit_issues) + "\n\n"
    if file_sec_issues:
        context += "## File Security Issues\n" + "\n".join(file_sec_issues)
        
    return context.strip() or "The review did not identify any security vulnerabilities requiring urgent attention."

def get_summarize_report_context(review_context):
    master_review = review_context.get("master_review", "")
    exec_assess = get_markdown_section_content(master_review, ["executive assessment", "executive summary"])
    verdict = get_markdown_section_content(master_review, ["final verdict"])
    
    overall_risk = ""
    for line in master_review.splitlines():
        if "overall risk:" in line.lower() or "risk level:" in line.lower():
            overall_risk = line.strip()
            break
            
    has_exec = False
    if exec_assess:
        exec_clean = exec_assess.replace("## Executive Assessment", "").strip().lower()
        if exec_clean and "none" not in exec_clean:
            has_exec = True
            
    context = ""
    if has_exec:
        context += f"{exec_assess}\n\n"
    if verdict:
        context += f"{verdict}\n\n"
    if overall_risk:
        context += f"## Overall Risk\n* {overall_risk}\n"
        
    return context.strip() or "The review indicates a generally stable project with no major issues requiring immediate action."

def get_architecture_context(review_context):
    arch = review_context.get("architecture_analysis", "").strip()
    if not arch or "none identified" in arch.lower():
        return "The review did not identify significant architectural concerns. The detected structure appears appropriate for the current project scope."
    return arch

def get_dependency_context(review_context):
    dep = review_context.get("dependency_analysis", "").strip()
    if not dep or "no vulnerable dependencies" in dep.lower() or "none identified" in dep.lower():
        return "No vulnerable dependencies were detected during dependency analysis. Current dependency health appears acceptable."
    return dep

# ==========================================
# CUSTOM QUESTION CONTEXT REDUCTION
# ==========================================

def extract_relevant_context_from_struct(review_context, question):
    if not review_context:
        return ""
        
    question_lower = question.lower()
    file_reviews = review_context.get("file_reviews", {})
    files_mentioned = []
    
    for filename in file_reviews:
        if filename.lower() in question_lower:
            files_mentioned.append(filename)
            
    if files_mentioned:
        if len(files_mentioned) > 1:
            context_parts = []
            for filename in files_mentioned:
                context_parts.append(f"# File Review: {filename}\n{file_reviews[filename]}")
            return "\n\n".join(context_parts)
            
        filename = files_mentioned[0]
        context = f"# File Review: {filename}\n{file_reviews[filename]}\n\n"
        
        master_review = review_context.get("master_review", "")
        if any(k in question_lower for k in ["security", "vulnerability", "risk", "exploit", "auth", "impact", "why"]):
            sec_sec = get_markdown_section_content(master_review, ["security assessment", "critical issues"])
            if sec_sec:
                context += f"{sec_sec}\n"
        if any(k in question_lower for k in ["improve", "fix", "priority", "recommendation", "action", "how"]):
            recs_sec = get_markdown_section_content(master_review, ["recommended actions", "critical issues"])
            if recs_sec:
                context += f"{recs_sec}\n"
        return context.strip()
        
    context_parts = []
    master_review = review_context.get("master_review", "")
    
    if any(k in question_lower for k in ["security", "vulnerability", "risk", "exploit"]):
        sec_sec = get_markdown_section_content(master_review, ["security assessment", "critical issues"])
        if sec_sec:
            context_parts.append(sec_sec)
            
    if any(k in question_lower for k in ["architecture", "structure", "design"]):
        arch_sec = review_context.get("architecture_analysis", "")
        if arch_sec:
            context_parts.append(arch_sec)
            
    if any(k in question_lower for k in ["dependency", "package", "library"]):
        dep_sec = review_context.get("dependency_analysis", "")
        if dep_sec:
            context_parts.append(dep_sec)
            
    if any(k in question_lower for k in ["duplicate", "repeated"]):
        dup_sec = review_context.get("duplicate_analysis", "")
        if dup_sec:
            context_parts.append(dup_sec)
            
    if any(k in question_lower for k in ["fix", "priority", "improve", "recommendation", "bug", "issue", "problem"]):
        crit_sec = get_markdown_section_content(master_review, ["critical issues", "recommended actions"])
        if crit_sec:
            context_parts.append(crit_sec)
            
    if context_parts:
        return "\n\n".join(context_parts).strip()
        
    stopwords = {
        "what", "is", "the", "a", "about", "this", "in", "on", "of", "to", "for", 
        "and", "how", "why", "are", "you", "do", "i", "can", "please", "explain",
        "should", "we", "with", "from", "at", "what's"
    }
    words = [w.strip("?,.!") for w in question_lower.split() if w.strip("?,.!") not in stopwords]
    matched_sections = []
    master_sections = split_report_by_headings(master_review)
    for word in words:
        if len(word) > 2:
            for heading, content in master_sections.items():
                if word in heading.lower():
                    if content not in matched_sections:
                        matched_sections.append(content)
                        
    if matched_sections:
        return "\n\n".join(matched_sections).strip()
        
    default_parts = []
    exec_assess = get_markdown_section_content(master_review, ["executive assessment", "executive summary"])
    if exec_assess:
        default_parts.append(exec_assess)
    crit_issues = get_markdown_section_content(master_review, ["critical issues"])
    if crit_issues:
        default_parts.append(crit_issues)
    recs = get_markdown_section_content(master_review, ["recommended actions"])
    if recs:
        default_parts.append(recs)
        
    if default_parts:
        return "\n\n".join(default_parts).strip()
        
    fallback_text = (
        f"# PROJECT LEVEL ANALYSIS\n\n{master_review}\n\n"
        f"{review_context.get('architecture_analysis', '')}\n\n"
        f"{review_context.get('dependency_analysis', '')}\n\n"
        f"{review_context.get('duplicate_analysis', '')}"
    )
    return fallback_text.strip()

# ==========================================
# PROMPT ENGINEERING & CHAT ROUTING
# ==========================================

def build_chat_prompt(relevant_context, question, history=None, is_button=False):
    history_str = ""
    if history:
        for msg in history:
            role = getattr(msg, "role", None) or msg.get("role", "")
            content = getattr(msg, "content", None) or msg.get("content", "")
            role_label = "User" if role == "user" else "Assistant"
            history_str += f"{role_label}: {content}\n"
            
    role_desc = "Senior Code Reviewer, Senior Security Reviewer, and Senior Software Architect"
    
    if is_button:
        word_limit_instruction = """- Target response length: 100 to 120 words.
        - STRICT MAXIMUM length: 150 words."""
    else:
        word_limit_instruction = """- Target response length: 150 to 180 words.
        - STRICT MAXIMUM length: 250 words."""

    prompt = f"""You are a {role_desc}.
    
    You are analyzing a structured code review context.

    Your task:
    - Explain, prioritize, interpret, and assess the impact of the findings in the context.
    - The review findings in the context are your evidence; your explanation is the output.
    - Do NOT repeat report text verbatim.
    - Do NOT generate another review report.
    - Do NOT dump raw findings.

    CRITICAL RULES:
    {word_limit_instruction}
    - Do NOT generate large essays or long paragraphs. Use concise bullet points where appropriate.
    - Only explain findings that exist in the context. Do NOT invent/hallucinate vulnerabilities, files, architecture risks, or dependency risks.
    - If a category contains no findings, do NOT provide generic best practices. Instead, explain why the review result is positive (e.g., explain that dependency health of the reviewed project appears acceptable, or no critical issues were identified).
    - Do not suggest unrelated best practices.
    - Never repeat context verbatim.
    - When explaining security risks (e.g., 'Explain Security Risks'): if the review contains hardcoded secrets, tokens, or credentials, you MUST explain the risks of those hardcoded secrets and recommend environment variable practices.
    - When asked to prioritize fixes (e.g., 'What Should I Fix First?'): you MUST prioritize findings in the following order: (1) SQL Injection, (2) Hardcoded Secrets, (3) Authentication Issues, (4) Weak Cryptography, (5) Lower-priority improvements.

    Context:
    {relevant_context}

    Conversation History:
    {history_str}

    Question:
    {question}

    Answer:
    """
    return prompt

def ask_review_question(report_text, question, history=None, review_context=None):
    if not report_text or not question:
        return "Not mentioned in the review report."
        
    if not review_context:
        review_context = build_review_context(report_text)
        
    predefined_questions = {
        "Explain Critical Issues": get_critical_issues_context,
        "What Should I Fix First?": get_fix_prioritization_context,
        "Explain Security Risks": get_security_risks_context,
        "Summarize Report": get_summarize_report_context,
        "Explain Architecture Analysis": get_architecture_context,
        "Explain Dependency Security Analysis": get_dependency_context,
        
        # Detailed prompts
        "Explain the critical issues found in this review. For each issue explain:\n- why it occurs\n- possible impact\n- risk severity\n- recommended fix\n\nUse only findings present in the review.\nMaximum 150 words.": get_critical_issues_context,
        
        "Based only on the review findings, prioritize all issues from highest risk to lowest risk.\n\nExplain:\n- what should be fixed first\n- why it is highest priority\n- recommended order of implementation\n\nMaximum 150 words.": get_fix_prioritization_context,
        
        "Explain only the security findings identified in the review.\n\nInclude:\n- security risk\n- attack impact\n- business impact\n- recommended remediation\n\nUse only findings present in the review.\n\nMaximum 150 words.": get_security_risks_context,
        
        "Provide a concise executive summary of the review.\n\nInclude:\n- overall project health\n- major findings\n- release readiness\n\nMaximum 150 words.": get_summarize_report_context,
        
        "Explain the architecture analysis section.\n\nInclude:\n- detected project structure\n- architecture observations\n- actual risks identified\n\nIf no architecture risks exist, explain why the architecture appears acceptable.\n\nMaximum 150 words.": get_architecture_context,
        
        "Explain the dependency security analysis findings.\n\nIf vulnerable dependencies exist:\n- explain risks\n- explain impact\n- recommend upgrades\n\nIf no vulnerable dependencies exist:\n- explain that dependency health appears acceptable\n\nMaximum 150 words.": get_dependency_context
    }
    
    is_button = question in predefined_questions
    
    start_time = time.time()
    
    review_context_hash = get_context_hash(review_context)
    cache_key = (review_context_hash, question.lower())
    
    cached_answer = chat_cache.get(cache_key)
    if cached_answer is not None:
        elapsed = time.time() - start_time
        print(f"Chat Time: {elapsed:.4f} sec")
        print("Context Size: 0 chars (Cached)")
        print(f"Answer Size: {len(cached_answer)} chars")
        print("Cache: HIT")
        return cached_answer
        
    if is_button:
        relevant_context = predefined_questions[question](review_context)
    else:
        relevant_context = extract_relevant_context_from_struct(review_context, question)
        
    print(f"Context Reduction Selection for question '{question}':")
    print(f"  Context Size: {len(relevant_context)} chars")
    
    # Empty result bypass logic to guarantee 100% accuracy and zero hallucination on clean files
    empty_messages = {
        "The review did not identify any critical issues requiring immediate remediation.",
        "The review did not identify any security vulnerabilities requiring urgent attention.",
        "The review did not identify significant architectural concerns. The detected structure appears appropriate for the current project scope.",
        "No vulnerable dependencies were detected during dependency analysis. Current dependency health appears acceptable.",
        "No high-priority fixes were identified. Focus can remain on general maintainability and code quality improvements.",
        "The review indicates a generally stable project with no major issues requiring immediate action."
    }
    
    if relevant_context in empty_messages:
        elapsed = time.time() - start_time
        print(f"Chat Time (Direct Empty Response): {elapsed:.4f} sec")
        chat_cache.put(cache_key, relevant_context)
        return relevant_context
        
    prompt = build_chat_prompt(relevant_context, question, history, is_button=is_button)
    
    try:
        answer = chat_llm.invoke(prompt)
        answer_str = answer.strip()
        chat_cache.put(cache_key, answer_str)
        
        elapsed = time.time() - start_time
        print(f"Chat Time: {elapsed:.4f} sec")
        print(f"Context Size: {len(relevant_context)} chars")
        print(f"Prompt Size: {len(prompt)} chars")
        print(f"Answer Size: {len(answer_str)} chars")
        print("Cache: MISS")
        
        return answer_str
    except Exception as e:
        print(f"Error in ask_review_question: {e}")
        return "Error calling the AI Review Assistant. Please make sure Ollama is running."

def ask_review_question_stream(report_text, question, history=None, review_context=None):
    if not report_text or not question:
        yield "Not mentioned in the review report."
        return
        
    if not review_context:
        review_context = build_review_context(report_text)
        
    predefined_questions = {
        "Explain Critical Issues": get_critical_issues_context,
        "What Should I Fix First?": get_fix_prioritization_context,
        "Explain Security Risks": get_security_risks_context,
        "Summarize Report": get_summarize_report_context,
        "Explain Architecture Analysis": get_architecture_context,
        "Explain Dependency Security Analysis": get_dependency_context,
        
        # Detailed prompts
        "Explain the critical issues found in this review. For each issue explain:\n- why it occurs\n- possible impact\n- risk severity\n- recommended fix\n\nUse only findings present in the review.\nMaximum 150 words.": get_critical_issues_context,
        
        "Based only on the review findings, prioritize all issues from highest risk to lowest risk.\n\nExplain:\n- what should be fixed first\n- why it is highest priority\n- recommended order of implementation\n\nMaximum 150 words.": get_fix_prioritization_context,
        
        "Explain only the security findings identified in the review.\n\nInclude:\n- security risk\n- attack impact\n- business impact\n- recommended remediation\n\nUse only findings present in the review.\n\nMaximum 150 words.": get_security_risks_context,
        
        "Provide a concise executive summary of the review.\n\nInclude:\n- overall project health\n- major findings\n- release readiness\n\nMaximum 150 words.": get_summarize_report_context,
        
        "Explain the architecture analysis section.\n\nInclude:\n- detected project structure\n- architecture observations\n- actual risks identified\n\nIf no architecture risks exist, explain why the architecture appears acceptable.\n\nMaximum 150 words.": get_architecture_context,
        
        "Explain the dependency security analysis findings.\n\nIf vulnerable dependencies exist:\n- explain risks\n- explain impact\n- recommend upgrades\n\nIf no vulnerable dependencies exist:\n- explain that dependency health appears acceptable\n\nMaximum 150 words.": get_dependency_context
    }
    
    is_button = question in predefined_questions
    
    start_time = time.time()
    
    review_context_hash = get_context_hash(review_context)
    cache_key = (review_context_hash, question.lower())
    
    cached_answer = chat_cache.get(cache_key)
    if cached_answer is not None:
        elapsed = time.time() - start_time
        print(f"Chat Time (Stream Cache Hit): {elapsed:.4f} sec")
        yield cached_answer
        return
        
    if is_button:
        relevant_context = predefined_questions[question](review_context)
    else:
        relevant_context = extract_relevant_context_from_struct(review_context, question)
        
    print(f"Context Reduction Selection for stream question '{question}':")
    print(f"  Context Size: {len(relevant_context)} chars")
    
    empty_messages = {
        "The review did not identify any critical issues requiring immediate remediation.",
        "The review did not identify any security vulnerabilities requiring urgent attention.",
        "The review did not identify significant architectural concerns. The detected structure appears appropriate for the current project scope.",
        "No vulnerable dependencies were detected during dependency analysis. Current dependency health appears acceptable.",
        "No high-priority fixes were identified. Focus can remain on general maintainability and code quality improvements.",
        "The review indicates a generally stable project with no major issues requiring immediate action."
    }
    
    if relevant_context in empty_messages:
        elapsed = time.time() - start_time
        print(f"Chat Time (Stream Direct Empty Response): {elapsed:.4f} sec")
        chat_cache.put(cache_key, relevant_context)
        yield relevant_context
        return
        
    prompt = build_chat_prompt(relevant_context, question, history, is_button=is_button)
    
    full_response = []
    try:
        # Stream from Ollama model
        for chunk in chat_llm.stream(prompt):
            yield chunk
            full_response.append(chunk)
            
        full_str = "".join(full_response).strip()
        if full_str:
            chat_cache.put(cache_key, full_str)
            
        elapsed = time.time() - start_time
        print(f"Chat Time (Stream Complete): {elapsed:.4f} sec")
        print(f"Context Size: {len(relevant_context)} chars")
        print(f"Prompt Size: {len(prompt)} chars")
        print(f"Answer Size: {len(full_str)} chars")
    except Exception as e:
        print(f"Error in ask_review_question_stream: {e}")
        yield "Error calling the AI Review Assistant. Please make sure Ollama is running."

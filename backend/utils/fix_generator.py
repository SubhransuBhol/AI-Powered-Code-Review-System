from utils.severity_mapper import get_severity

FIX_TEMPLATES = {
    "sql_injection": 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
    "hardcoded_password": 'import os\npassword = os.getenv("APP_PASSWORD")',
    "input_validation": 'if not input_data or not isinstance(input_data, str):\n    raise ValueError("Invalid input")',
    "error_handling": 'try:\n    # Perform operation\nexcept Exception as e:\n    logger.error(f"Operation failed: {e}")',
    "unsafe_file": 'with open(safe_path, "r", encoding="utf-8") as f:\n    data = f.read()'
}

def get_fix_category_and_template(issue_text):
    text = issue_text.lower()
    
    # SQL Injection
    if "sql injection" in text or "b608" in text:
        return "sql_injection", FIX_TEMPLATES["sql_injection"]
        
    # Hardcoded Password
    if "hardcoded password" in text or "password is hardcoded" in text or "jwt" in text or "b105" in text:
        return "hardcoded_password", FIX_TEMPLATES["hardcoded_password"]
        
    # Input Validation
    if "input validation" in text:
        return "input_validation", FIX_TEMPLATES["input_validation"]
        
    # Error Handling
    if "error handling" in text:
        return "error_handling", FIX_TEMPLATES["error_handling"]
        
    # Unsafe File Operations
    if "file operation" in text or "unsafe file" in text or "open(" in text:
        return "unsafe_file", FIX_TEMPLATES["unsafe_file"]
        
    return None, None

def get_fix_for_issue(issue_text):
    _, template = get_fix_category_and_template(issue_text)
    return template

def add_fixes_to_review(review_text):
    lines = []
    suggested_categories = set()
    
    for line in review_text.splitlines():
        lines.append(line)
        stripped = line.strip()
        if stripped.startswith("* "):
            issue = stripped[2:]
            severity = None
            actual_issue = issue
            
            # Check if severity is already prefixed, e.g. [CRITICAL] or [HIGH]
            if issue.startswith("[") and "]" in issue:
                parts = issue.split("]", 1)
                severity = parts[0][1:].upper()
                actual_issue = parts[1].strip()
            else:
                severity = get_severity(issue)
            
            if severity in ("HIGH", "CRITICAL"):
                category, fix = get_fix_category_and_template(actual_issue)
                if fix and category:
                    # Deduplicate using the stable category/vulnerability type
                    if category not in suggested_categories:
                        suggested_categories.add(category)
                        # Indent each line of the fix by two spaces
                        indented_fix = "\n".join([f"  {l}" for l in fix.splitlines()])
                        lines.append(f"  Suggested Fix:\n{indented_fix}")
                        
    return "\n".join(lines)

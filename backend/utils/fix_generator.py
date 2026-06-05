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

def generate_secret_recommendations(filename, content, has_env_file):
    import re
    keys = [
        "password", "passwd", "secret", "api_key", "apikey", "token", "jwt_secret", 
        "client_secret", "private_key", "access_key", "access_token", "refresh_token", 
        "bearer_token", "api_token", "aws_access_key", "aws_secret_key", "database_url", 
        "connection_string"
    ]
    
    sorted_keys = sorted(keys, key=len, reverse=True)
    pattern = re.compile(r'\b(\w*(?:' + '|'.join(sorted_keys) + r')\w*)\s*=\s*[\'"]([^\'"]+)[\'"]', re.IGNORECASE)
    matches = pattern.findall(content)
    
    detected_keys = []
    for match in matches:
        key_name, val = match
        if val.strip() and key_name not in detected_keys:
            detected_keys.append(key_name)
            
    if not detected_keys:
        return ""
        
    rec = "--------------------------------------------------\n"
    rec += "Secret Management Recommendation\n"
    rec += "--------------------------------------------------\n\n"
    
    if detected_keys:
        rec += "Detected hardcoded credential:\n"
        for k in detected_keys:
            rec += f"- {k}\n"
        rec += "\n"
        
    rec += "Recommendation:\n"
    rec += "Move sensitive values into environment variables.\n\n"
    
    has_password_secret = any("password" in k.lower() or "passwd" in k.lower() for k in detected_keys)
    if has_password_secret:
        rec += "For password storage, do NOT use MD5, SHA-1, or plain SHA-256. Instead, use a secure cryptographic hashing algorithm. Recommended choices in order of preference:\n"
        rec += "1. Argon2 (preferred)\n"
        rec += "2. bcrypt\n"
        rec += "3. scrypt\n\n"
        
    rec += "Example:\n\n"
    rec += ".env\n\n"
    if detected_keys:
        for k in detected_keys:
            rec += f"{k.upper()}=your_{k.lower()}\n"
    else:
        rec += "API_KEY=your_api_key\n"
    rec += "\n"
    
    rec += "Python:\n\n"
    rec += "import os\n\n"
    if detected_keys:
        for k in detected_keys:
            rec += f"{k.upper()} = os.getenv(\"{k.upper()}\")\n"
    else:
        rec += "API_KEY = os.getenv(\"API_KEY\")\n"
    rec += "\n"
    
    rec += "Benefits:\n"
    rec += "- prevents credential leakage\n"
    rec += "- safer deployments\n"
    rec += "- easier secret rotation\n"
    
    if not has_env_file:
        rec += "\nNote: A `.env` file was not detected in this repository. It is highly recommended to create one to manage local environment variables securely.\n"
        
    return rec

def check_config_security(filename, content):
    import re
    config_filenames = [".env", ".env.example", "config.py", "settings.py", "config.json", "config.yaml", "config.yml", "application.properties"]
    if not any(cfg in filename.lower() for cfg in config_filenames):
        return []
        
    findings = []
    
    # Scan for insecure configurations
    debug_patterns = [
        (re.compile(r'\bDEBUG\s*=\s*True\b', re.IGNORECASE), "Debug mode is enabled (DEBUG = True) and should be disabled in production deployments."),
        (re.compile(r'\bFLASK_DEBUG\s*=\s*(True|1)\b', re.IGNORECASE), "Debug mode is enabled (FLASK_DEBUG = True) and should be disabled in production deployments."),
        (re.compile(r'\bAPP_DEBUG\s*=\s*(True|1)\b', re.IGNORECASE), "Debug mode is enabled (APP_DEBUG = True) and should be disabled in production deployments."),
        (re.compile(r'\bNODE_ENV\s*=\s*[\'"]?development[\'"]?\b', re.IGNORECASE), "Development environment is configured (NODE_ENV=development) and should be set to production in production deployments.")
    ]
    
    for pattern, message in debug_patterns:
        if pattern.search(content):
            findings.append(message)
            
    # Check general development flags
    if "development-only" in content.lower() or "dev config" in content.lower():
        findings.append("Development-only configuration is enabled and should be disabled in production deployments.")
        
    return findings

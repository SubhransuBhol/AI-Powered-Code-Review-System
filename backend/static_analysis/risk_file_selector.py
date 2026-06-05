import os
import re
import sys

# Add the current python executable's directory to PATH so subprocesses can find venv scripts like bandit
sys_path_dir = os.path.dirname(sys.executable)
if sys_path_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = sys_path_dir + os.pathsep + os.environ.get("PATH", "")

MAX_RISK_FILES = 5

def score_file_risk(filename, content, filepath):
    """
    Computes a risk score for a given file based on filename, content, and Bandit results.
    """
    filename_score = 0
    base = os.path.basename(filename).lower()
    
    # Filename Risk Scoring
    # Critical Security Files (15)
    security_keywords = ["auth", "login", "jwt", "token", "security", "permission", "role"]
    if any(kw in base for kw in security_keywords):
        filename_score += 15
        
    # Database/Data Access (10)
    db_keywords = ["database", "db", "repository", "model"]
    if any(kw in base for kw in db_keywords):
        filename_score += 10
        
    # Configuration Files (10)
    config_keywords = ["config", "settings", "env", "secret"]
    if any(kw in base for kw in config_keywords):
        filename_score += 10
        
    # Business-Critical Files (15)
    business_keywords = ["payment", "billing", "checkout", "order"]
    if any(kw in base for kw in business_keywords):
        filename_score += 15

    # Content Risk Scoring
    content_score = 0
    if content:
        # Secrets (10)
        secrets_rx = re.compile(r'\b(password|secret|api_key|access_key|private_key|token|jwt_secret)\s*=\s*', re.IGNORECASE)
        content_score += len(secrets_rx.findall(content)) * 10
        
        # SQL Injection (5) and f-strings in SQL (10)
        cursor_execute_rx = re.compile(r'cursor\.execute\s*\(', re.IGNORECASE)
        execute_rx = re.compile(r'\bexecute\s*\(', re.IGNORECASE)
        sql_keywords_rx = re.compile(r'\b(SELECT|INSERT|UPDATE|DELETE)\b', re.IGNORECASE)
        f_sql_rx = re.compile(r'f["\']{1,3}[^"\']*\b(SELECT|INSERT|UPDATE|DELETE)\b[^{]*\{', re.IGNORECASE)
        
        content_score += len(cursor_execute_rx.findall(content)) * 5
        content_score += len(execute_rx.findall(content)) * 5
        content_score += len(sql_keywords_rx.findall(content)) * 5
        content_score += len(f_sql_rx.findall(content)) * 10
        
        # Dangerous Execution (10)
        eval_rx = re.compile(r'\beval\s*\(')
        exec_rx = re.compile(r'\bexec\s*\(')
        os_system_rx = re.compile(r'\bos\.system\s*\(')
        sub_run_rx = re.compile(r'\bsubprocess\.run\s*\(')
        sub_popen_rx = re.compile(r'\bsubprocess\.Popen\s*\(')
        sub_call_rx = re.compile(r'\bsubprocess\.call\s*\(')
        shell_true_rx = re.compile(r'\bshell\s*=\s*True\b', re.IGNORECASE)
        
        content_score += len(eval_rx.findall(content)) * 10
        content_score += len(exec_rx.findall(content)) * 10
        content_score += len(os_system_rx.findall(content)) * 10
        content_score += len(sub_run_rx.findall(content)) * 10
        content_score += len(sub_popen_rx.findall(content)) * 10
        content_score += len(sub_call_rx.findall(content)) * 10
        content_score += len(shell_true_rx.findall(content)) * 10
        
        # Insecure Serialization (10)
        pickle_loads_rx = re.compile(r'\bpickle\.loads\s*\(')
        yaml_load_rx = re.compile(r'\byaml\.load\s*\(')
        
        content_score += len(pickle_loads_rx.findall(content)) * 10
        content_score += len(yaml_load_rx.findall(content)) * 10
        
        # Weak Cryptography (5)
        md5_rx = re.compile(r'\bmd5\s*\(', re.IGNORECASE)
        sha1_rx = re.compile(r'\bsha1\s*\(', re.IGNORECASE)
        
        content_score += len(md5_rx.findall(content)) * 5
        content_score += len(sha1_rx.findall(content)) * 5
        
        # SSL/TLS Misconfiguration (10)
        verify_false_rx = re.compile(r'\bverify\s*=\s*False\b', re.IGNORECASE)
        ssl_unverified_rx = re.compile(r'\bssl\._create_unverified_context\b')
        
        content_score += len(verify_false_rx.findall(content)) * 10
        content_score += len(ssl_unverified_rx.findall(content)) * 10
        
        # Authentication Logic (5)
        auth_logic_rx = re.compile(r'\b(jwt|authenticate|authorization|login)\b', re.IGNORECASE)
        content_score += len(auth_logic_rx.findall(content)) * 5
        
        # Network Operations (2)
        requests_rx = re.compile(r'\brequests\b', re.IGNORECASE)
        http_rx = re.compile(r'https?://', re.IGNORECASE)
        
        content_score += len(requests_rx.findall(content)) * 2
        content_score += len(http_rx.findall(content)) * 2

    # Bandit Integration
    bandit_score = 0
    if filepath and filename.lower().endswith(".py") and os.path.exists(filepath):
        from static_analysis.bandit_runner import run_bandit
        try:
            findings = run_bandit(filepath)
            bandit_score = 10 * len(findings)
        except Exception as e:
            print(f"Error running Bandit on {filepath}: {e}")
            
    return filename_score + content_score + bandit_score

def detect_risky_files(files):
    """
    Scans all files, computes risk scores, sorts descending, and returns:
    (top_risky_files, all_scores_dict)
    where:
      top_risky_files: top MAX_RISK_FILES with score > 0
      all_scores_dict: dict of {filename: score} for all files with score > 0
    """
    scored_files = []
    all_scores_dict = {}
    for f in files:
        filename = f.get("filename", "")
        content = f.get("content", "")
        filepath = f.get("filepath")
        
        score = score_file_risk(filename, content, filepath)
        if score > 0:
            all_scores_dict[filename] = score
            scored_files.append({
                "filename": filename,
                "filepath": filepath,
                "content": content,
                "source": "risk",
                "risk_score": score
            })
            
    # Sort descending by risk score
    scored_files.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return scored_files[:MAX_RISK_FILES], all_scores_dict

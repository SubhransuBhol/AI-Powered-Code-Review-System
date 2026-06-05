import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.file_reader import build_lightweight_context
from utils.fix_generator import generate_secret_recommendations, check_config_security
from services.master_review_builder import build_score, validate_and_fix_consistency, final_report_count_validator
from utils.architecture_analyzer import analyze_architecture

def test_lightweight_context():
    print("=== Testing Lightweight Context Builder ===")
    all_files = [
        {
            "filename": "auth.py",
            "content": "import jwt\ndef login(username, password):\n    pass\nclass UserSession:\n    pass"
        },
        {
            "filename": "api.py",
            "content": "from auth import login\ndef handle_request():\n    login('admin', 'admin123')"
        }
    ]
    selected = ["api.py"]
    context = build_lightweight_context(all_files, selected, "Backend API Application")
    print(context)
    
    assert "Backend API Application" in context
    assert "api.py" in context
    assert "auth.py" in context
    assert "UserSession" in context
    assert "login" in context
    assert "Imports: auth" in context
    print("build_lightweight_context passed!")

def test_secret_recommendations():
    print("\n=== Testing Secret Recommendations ===")
    
    # 1. Test detecting hardcoded password
    content1 = 'db_password = "supersecretpassword123"'
    rec1 = generate_secret_recommendations("config.py", content1, has_env_file=False)
    print(rec1)
    
    assert "Secret Management Recommendation" in rec1
    assert "db_password" in rec1 or "DB_PASSWORD" in rec1 or "Detected hardcoded credential" in rec1
    assert "Argon2" in rec1
    assert "bcrypt" in rec1
    assert "scrypt" in rec1
    
    # 2. Test expanded secrets coverage (e.g. aws_access_key)
    content2 = 'AWS_ACCESS_KEY = "AKIAEXAMPLEKEY"'
    rec2 = generate_secret_recommendations("settings.py", content2, has_env_file=True)
    print(rec2)
    assert "AWS_ACCESS_KEY" in rec2 or "aws_access_key" in rec2 or "Detected hardcoded credential" in rec2
    
    # 3. Test that clean files return empty string (strict suppression)
    content3 = 'def hello():\n    print("no secrets here")'
    rec3 = generate_secret_recommendations("helper.py", content3, has_env_file=False)
    print("Clean file recommendation block:", repr(rec3))
    assert rec3 == "", f"Expected empty string for secret recommendations, got: {rec3}"
    
    print("generate_secret_recommendations passed!")

def test_config_security_checks():
    print("\n=== Testing Configuration Security Checks ===")
    
    # 1. Test config.py with debug enabled
    content1 = "DEBUG = True\nPORT = 8080"
    findings1 = check_config_security("config.py", content1)
    print("Findings for config.py:", findings1)
    assert len(findings1) == 1
    assert "Debug mode is enabled" in findings1[0]
    
    # 2. Test non-config file (should not produce findings even if DEBUG = True exists)
    content2 = "DEBUG = True\n"
    findings2 = check_config_security("helper.py", content2)
    print("Findings for helper.py:", findings2)
    assert len(findings2) == 0
    
    print("check_config_security passed!")

def test_score_calibration():
    print("\n=== Testing Score Calibration ===")
    
    # Case A: Clean project
    score_clean = build_score(0, 0, 0, critical_findings=[], architecture_risk="LOW", has_duplicates=False)
    print("Clean score:", score_clean)
    assert "10/10" in score_clean
    
    # Case B: Balanced scoring with deductions
    # Deductions:
    # 1 Critical: -1.5
    # 1 High: -1.0
    # 1 Medium: -0.5
    # 1 Low/Improvement: -0.1
    # Total deduction = 3.1. Score = 10 - 3.1 = 6.9 -> rounds to 7/10!
    critical_findings = [
        "[CRITICAL] SQL Injection in database.py",
        "[HIGH] Hardcoded password in auth.py",
        "[MEDIUM] Weak MD5 usage in crypto.py"
    ]
    score_issues = build_score(0, 0, 1, critical_findings=critical_findings, architecture_risk="LOW", has_duplicates=False)
    print("Balanced score for 3 security findings + 1 improvement:", score_issues)
    assert "7/10" in score_issues
    
    # Case C: Balanced score with severe critical findings (should be 6/10 due to caps)
    critical_findings_bad = [
        "[CRITICAL] SQL Injection 1",
        "[CRITICAL] SQL Injection 2",
        "[CRITICAL] SQL Injection 3",
        "[CRITICAL] SQL Injection 4",
        "[CRITICAL] SQL Injection 5"
    ]
    score_bad = build_score(5, 5, 0, critical_findings=critical_findings_bad, architecture_risk="HIGH", has_duplicates=True)
    print("Bad score:", score_bad)
    assert "6/10" in score_bad
    
    # Case D: Worst possible project hitting the minimum boundary (1/10)
    critical_findings_worst = [
        "[CRITICAL] SQL Injection 1",
        "[CRITICAL] SQL Injection 2",
        "[HIGH] Hardcoded secrets 1",
        "[HIGH] Hardcoded secrets 2",
        "[MEDIUM] MD5 hashing 1",
        "[MEDIUM] MD5 hashing 2",
        "[MEDIUM] MD5 hashing 3",
        "[LOW] Missing header 1",
        "[LOW] Missing header 2",
    ]
    score_worst = build_score(0, 0, 10, critical_findings=critical_findings_worst, architecture_risk="HIGH", has_duplicates=True)
    print("Worst score (minimum cap):", score_worst)
    assert "1/10" in score_worst
    
    print("build_score passed!")

def test_consistency_validation():
    print("\n=== Testing Consistency Validation ===")
    
    # 1. Test safety claims suppression
    llm_sections = {
        "executive": "The repository is a safe repository with robust security design.",
        "security": "Our review shows robust security posture and secure design.",
        "verdict": "The project is production ready and safe."
    }
    critical_findings = ["[CRITICAL] SQL Injection in db.py"]
    validated = validate_and_fix_consistency(
        llm_sections.copy(),
        critical_findings=critical_findings,
        total_security=1,
        overall_risk="HIGH",
        high_risk_files=["db.py"],
        all_reviews_text="SQL Injection detected in db.py"
    )
    print("Validated Sections:")
    for k, v in validated.items():
        print(f"{k}: {v}")
    assert "safe repository" not in validated["executive"].lower()
    assert "robust security" not in validated["executive"].lower()
    assert "robust security" not in validated["security"].lower()
    assert "secure design" not in validated["security"].lower()
    assert "not production ready" in validated["verdict"].lower()
    
    # 2. Test count consistency validation (improvements and bugs)
    llm_sections_counts = {
        "executive": "Executive Summary: Total Improvements Suggested: 26. Later: 44 suggested improvements. 15 bugs found.",
        "strengths": "29 improvements suggested for better code quality and security.",
        "weaknesses": "There are 44 improvements that can be made.",
        "security": "Total vulnerabilities is 12.",
        "verdict": "Total improvements suggested: 5."
    }
    validated_counts = validate_and_fix_consistency(
        llm_sections_counts.copy(),
        critical_findings=[],
        total_security=3,
        overall_risk="MEDIUM",
        high_risk_files=[],
        all_reviews_text="",
        total_bugs=2,
        total_improvements=5
    )
    print("Validated Counts Sections:")
    for k, v in validated_counts.items():
        print(f"{k}: {v}")
    assert "several improvements identified" in validated_counts["executive"].lower()
    assert "26" not in validated_counts["executive"].lower()
    assert "44" not in validated_counts["executive"].lower()
    assert "functional issues identified" in validated_counts["executive"].lower()
    assert "15" not in validated_counts["executive"].lower()
    assert "29" not in validated_counts["strengths"].lower()
    assert "several improvements identified" in validated_counts["strengths"].lower()
    assert "44" not in validated_counts["weaknesses"].lower()
    assert "several improvements identified" in validated_counts["weaknesses"].lower()
    assert "multiple security concerns detected" in validated_counts["security"].lower()
    assert "12" not in validated_counts["security"].lower()
    assert "several improvements identified" in validated_counts["verdict"].lower()
    
    print("validate_and_fix_consistency passed!")

def test_architecture_risk_decoupling():
    print("\n=== Testing Architecture Risk Decoupling ===")
    
    # Root-only project layout (no subfolders) but has layer separation:
    # - auth.py (Authentication)
    # - database.py (Database)
    # - api.py (API)
    # - crypto.py (Utility)
    # total 5 files in root.
    files_dict = {
        "auth.py": "def login(): pass",
        "database.py": "def query(): pass",
        "api.py": "def route(): pass",
        "crypto.py": "def hash(): pass",
        "payment.py": "def pay(): pass"
    }
    result = analyze_architecture(files_dict)
    print("Architecture Analysis:", result)
    # Should be MEDIUM instead of HIGH because of layers_count >= 2
    assert result["risk_level"] == "MEDIUM"
    
    print("test_architecture_risk_decoupling passed!")

def test_final_report_count_validator():
    print("\n=== Testing Final Report Count Validator ===")
    
    report_raw = (
        "# PROJECT LEVEL ANALYSIS\n\n"
        "## Executive Summary\n"
        "Total Improvements Suggested: 26\n\n"
        "## Strengths\n"
        "The project has a total of 29 improvements suggested for better code quality and security.\n"
        "There are 44 suggested improvements in total.\n"
        "We found 29 improvement suggestions here.\n"
        "There are 15 recommendations.\n\n"
        "## Weaknesses\n"
        "The project needs 29 improvements.\n"
        "Weakness: 44 areas of improvement identified."
    )
    
    validated_report = final_report_count_validator(
        report_raw,
        total_improvements=26,
        total_bugs=2,
        total_security=3
    )
    
    print("Validated Report:")
    print(validated_report)
    
    # Assert Executive Summary count is preserved
    assert "Total Improvements Suggested: 26" in validated_report
    
    # Assert narrative counts are removed and replaced qualitatively
    assert "29" not in validated_report
    assert "44" not in validated_report
    assert "15" not in validated_report
    assert "several improvements identified" in validated_report
    assert "improvement suggestions" in validated_report
    assert "recommendations were provided" in validated_report
    assert "improvement opportunities" in validated_report
    
    # Test specific phrase requested by user:
    # "The project shows some improvements with 29 total improvements."
    target_raw = (
        "## Strengths\n"
        "The project shows some improvements with 29 total improvements.\n"
    )
    validated_target = final_report_count_validator(
        target_raw,
        total_improvements=26,
        total_bugs=2,
        total_security=3
    )
    print("Validated Target Phrase:")
    print(validated_target)
    assert "The project shows some improvements with several improvements identified." in validated_target
    
    print("test_final_report_count_validator passed!")

if __name__ == "__main__":
    test_lightweight_context()
    test_secret_recommendations()
    test_config_security_checks()
    test_score_calibration()
    test_consistency_validation()
    test_architecture_risk_decoupling()
    test_final_report_count_validator()
    print("\nAll quality cleanup unit tests passed successfully!")

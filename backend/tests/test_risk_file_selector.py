import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from static_analysis.risk_file_selector import score_file_risk, detect_risky_files
from rag.hybrid_retriever import hybrid_retrieve

def test_scenarios():
    print("=== Testing Scenario Risk Scoring ===")
    
    # Scenario 1: auth.py with hardcoded password
    score1 = score_file_risk("auth.py", 'password = "admin123"', None)
    print(f"auth.py score: {score1}")
    # Filename match 'auth' (15) + Content 'password =' (10) = 25
    # Wait, 'password' keyword in password = "admin123" can also match auth logic 'login/authenticate/jwt/token/authorization'?
    # No, 'password' is not in auth logic keywords ("jwt", "authenticate", "authorization", "login").
    # So the expected score is 15 + 10 = 25. Let's assert score1 >= 25.
    assert score1 >= 25, f"Expected auth.py score to be >= 25, got {score1}"
    
    # Scenario 2: database.py with f-string SQL query
    score2 = score_file_risk("database.py", 'query = f"SELECT * FROM users WHERE id={user_id}"\ncursor.execute(query)', None)
    print(f"database.py score: {score2}")
    # Filename match 'database'/'db' (10) + 'SELECT' (5) + 'cursor.execute' (5) + f-string SQL (10) = 30
    assert score2 >= 30, f"Expected database.py score to be >= 30, got {score2}"
    
    # Scenario 3: config.py with API_KEY = "secret"
    score3 = score_file_risk("config.py", 'API_KEY = "secret"', None)
    print(f"config.py score: {score3}")
    # Filename match 'config'/'secret' (10) + Content 'API_KEY =' (10) = 20
    assert score3 >= 20, f"Expected config.py score to be >= 20, got {score3}"
    
    # Scenario 4: helper.py with eval(user_input)
    score4 = score_file_risk("helper.py", 'eval(user_input)', None)
    print(f"helper.py score: {score4}")
    # Filename match (0) + Content 'eval(' (10) = 10
    assert score4 >= 10, f"Expected helper.py score to be >= 10, got {score4}"
    
    # Scenario 5: clean.py
    score5 = score_file_risk("clean.py", 'def hello(): pass', None)
    print(f"clean.py score: {score5}")
    assert score5 == 0, f"Expected clean.py score to be 0, got {score5}"
    
    print("All individual scenarios scored correctly!")

def test_detect_risky_files():
    print("\n=== Testing detect_risky_files ===")
    files = [
        {"filename": "auth.py", "content": 'password = "admin123"', "filepath": None},
        {"filename": "database.py", "content": 'query = f"SELECT * FROM users WHERE id={user_id}"\ncursor.execute(query)', "filepath": None},
        {"filename": "config.py", "content": 'API_KEY = "secret"', "filepath": None},
        {"filename": "helper.py", "content": 'eval(user_input)', "filepath": None},
        {"filename": "clean.py", "content": 'def hello(): pass', "filepath": None}
    ]
    
    risky_files, scores = detect_risky_files(files)
    print("Risky Files detected:")
    for f in risky_files:
        print(f"- {f['filename']} (score: {f['risk_score']})")
        
    assert len(risky_files) == 4, f"Expected 4 risky files, got {len(risky_files)}"
    assert risky_files[0]["filename"] == "database.py" or risky_files[0]["filename"] == "auth.py"
    assert "clean.py" not in scores
    
    print("detect_risky_files works perfectly!")

def test_hybrid_retrieve_integration():
    print("\n=== Testing hybrid_retrieve Integration ===")
    # Mock retrieve_code to return no semantic files for simplicity
    from unittest.mock import patch
    with patch("rag.hybrid_retriever.retrieve_code") as mock_retrieve:
        mock_retrieve.return_value = {
            "ids": [["clean.py"]],
            "documents": [["def hello(): pass"]]
        }
        
        files = [
            {"filename": "auth.py", "content": 'password = "admin123"', "filepath": None},
            {"filename": "database.py", "content": 'query = f"SELECT * FROM users WHERE id={user_id}"\ncursor.execute(query)', "filepath": None},
            {"filename": "config.py", "content": 'API_KEY = "secret"', "filepath": None},
            {"filename": "helper.py", "content": 'eval(user_input)', "filepath": None},
            {"filename": "clean.py", "content": 'def hello(): pass', "filepath": None}
        ]
        
        result = hybrid_retrieve("test query", files)
        print("Hybrid retrieve returned files:")
        for f in result:
            print(f"- {f['filename']} (source: {f['source']})")
            
        # Check that:
        # 1. Priority files are included
        # 2. Risk files are included
        # 3. Semantic files fill remaining
        filenames = [f["filename"] for f in result]
        assert "auth.py" in filenames
        assert "database.py" in filenames
        assert "config.py" in filenames
        assert "helper.py" in filenames
        assert "clean.py" in filenames
        
        print("hybrid_retrieve integration works perfectly!")

if __name__ == "__main__":
    test_scenarios()
    test_detect_risky_files()
    test_hybrid_retrieve_integration()
    print("\nAll risk file selector tests passed!")

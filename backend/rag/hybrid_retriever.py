import os
from rag.retriever import retrieve_code

PRIORITY_KEYWORDS = [
    "auth",
    "login",
    "database",
    "db",
    "security",
    "user",
    "api",
    "config",
    "payment",
    "token",
    "jwt",
    "session",
    "admin",
    "credential"
]

CONTENT_PRIORITY_PATTERNS = [
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "password",
    "token",
    "jwt",
    "session",
    "login",
    "authenticate",
    "sqlite3",
    "cursor.execute",
    "execute(",
    "api_key",
    "secret"
]

def get_priority_files(files):
    """
    Filter files by priority keywords in filename or priority patterns in content.
    """
    priority_files = []
    for f in files:
        filename = f.get("filename", "")
        content = f.get("content", "")
        base = os.path.basename(filename).lower()
        
        is_prio = False
        for kw in PRIORITY_KEYWORDS:
            if kw.lower() in base:
                is_prio = True
                break
        
        if not is_prio:
            content_lower = content.lower()
            for pat in CONTENT_PRIORITY_PATTERNS:
                if pat.lower() in content_lower:
                    is_prio = True
                    break
        
        if is_prio:
            priority_files.append({
                "filename": filename,
                "filepath": f.get("filepath"),
                "content": content,
                "source": "priority"
            })
            
    return priority_files

def get_max_review_files(total_files):
    return min(
        40,
        max(20, int(total_files * 0.3))
    )

def hybrid_retrieve(query, all_files, semantic_top_k=5):
    """
    Retrieves project files using hybrid logic: Priority heuristic matches + Risk matches + Semantic matches.
    """
    from static_analysis.risk_file_selector import detect_risky_files

    # 1. Fetch priority heuristic matches
    priority_files = get_priority_files(all_files)
    
    # 2. Fetch risk-based matches
    risk_files, all_scores = detect_risky_files(all_files)
    
    # 3. Fetch semantic matches from ChromaDB
    results = retrieve_code(query, top_k=semantic_top_k)
    semantic_files = []
    semantic_scores_dict = {}
    file_map = {f["filename"]: f for f in all_files}
    
    if results and "ids" in results and results["ids"] and "documents" in results and results["documents"]:
        ids = results["ids"][0]
        documents = results["documents"][0]
        distances = results.get("distances", [[]])[0] if "distances" in results else [1.0] * len(ids)
        for i, (fid, doc) in enumerate(zip(ids, documents)):
            filepath = file_map.get(fid, {}).get("filepath")
            dist = distances[i] if i < len(distances) else 1.0
            sem_score = max(0.0, 10.0 - dist)
            semantic_scores_dict[fid] = sem_score
            semantic_files.append({
                "filename": fid,
                "content": doc,
                "filepath": filepath,
                "source": "semantic"
            })
            
    # 4. Score and Rank candidates: score = (priority_match * 100) + risk_score + semantic_score
    candidates = {}
    
    # Track priority files
    for f in priority_files:
        filename = f["filename"]
        candidates[filename] = {
            "file": f,
            "priority_match": 1,
            "risk_score": all_scores.get(filename, 0),
            "semantic_score": semantic_scores_dict.get(filename, 0.0)
        }
        
    # Track risk files
    for f in risk_files:
        filename = f["filename"]
        if filename not in candidates:
            candidates[filename] = {
                "file": {
                    "filename": filename,
                    "filepath": f.get("filepath"),
                    "content": f.get("content"),
                    "source": "risk"
                },
                "priority_match": 0,
                "risk_score": all_scores.get(filename, 0),
                "semantic_score": semantic_scores_dict.get(filename, 0.0)
            }
            
    # Track semantic files
    for f in semantic_files:
        filename = f["filename"]
        if filename not in candidates:
            candidates[filename] = {
                "file": f,
                "priority_match": 0,
                "risk_score": all_scores.get(filename, 0),
                "semantic_score": semantic_scores_dict.get(filename, 0.0)
            }
            
    # Calculate score for each candidate
    ranked_candidates = []
    for filename, data in candidates.items():
        score = (data["priority_match"] * 100) + data["risk_score"] + data["semantic_score"]
        ranked_candidates.append({
            "filename": filename,
            "file": data["file"],
            "score": score
        })
        
    # Sort descending by score
    ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
    
    max_review_files = get_max_review_files(len(all_files))
    selected_candidates = ranked_candidates[:max_review_files]
    merged = [c["file"] for c in selected_candidates]
            
    # 5. Log details (Temporary Verification Logging)
    print("=== FILE SELECTION ===")
    print("\nPriority Files:")
    for f in priority_files:
        print(f"- {f['filename']}")
    print("\nRisk Files:")
    for f in risk_files:
        print(f"- {f['filename']}")
    print("\nSemantic Files:")
    for f in semantic_files:
        print(f"- {f['filename']}")
    print(f"\nDynamic Review Limit: {max_review_files} (Total project files: {len(all_files)})")
    print("\nCandidate Ranking Scores:")
    for c in ranked_candidates:
        print(f"- {c['filename']}: Score = {c['score']:.2f}")
    print("\nFinal Selected Files:")
    for f in merged:
        print(f"- {f['filename']} ({f['source']})")
    print("\nRisk Scores:")
    for filename, score in sorted(all_scores.items(), key=lambda x: x[1], reverse=True):
        print(f"{filename} -> {score}")
    print("======================")
    
    return merged

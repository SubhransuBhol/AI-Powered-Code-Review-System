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

MAX_REVIEW_FILES = 8

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
                "content": content,
                "source": "priority"
            })
            
    return priority_files

def hybrid_retrieve(query, all_files, semantic_top_k=5):
    """
    Retrieves project files using hybrid logic: Priority heuristic matches + Semantic matches.
    """
    # 1. Fetch priority heuristic matches
    priority_files = get_priority_files(all_files)
    
    # 2. Fetch semantic matches from ChromaDB
    results = retrieve_code(query, top_k=semantic_top_k)
    semantic_files = []
    if results and "ids" in results and results["ids"] and "documents" in results and results["documents"]:
        ids = results["ids"][0]
        documents = results["documents"][0]
        for fid, doc in zip(ids, documents):
            semantic_files.append({
                "filename": fid,
                "content": doc,
                "source": "semantic"
            })
            
    # 3. Merge lists: Priority files first, then semantic files
    merged = []
    seen = set()
    
    for f in priority_files:
        filename = f["filename"]
        if filename not in seen:
            seen.add(filename)
            merged.append(f)
            
    for f in semantic_files:
        filename = f["filename"]
        if filename not in seen:
            seen.add(filename)
            merged.append(f)
            
    # 4. Cap final files to MAX_REVIEW_FILES
    final_files = merged[:MAX_REVIEW_FILES]
    
    # 5. Log details
    print("Priority Files:")
    print([f["filename"] for f in priority_files])
    print()
    print("Semantic Files:")
    print([f["filename"] for f in semantic_files])
    print()
    print("Final Files Selected:")
    print([(f["filename"], f["source"]) for f in final_files])
    
    return final_files

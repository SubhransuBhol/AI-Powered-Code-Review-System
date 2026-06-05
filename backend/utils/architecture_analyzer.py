import os
import re

def analyze_architecture(files_dict):
    """
    Analyzes files_dict (dict of {filename: content}) to perform rule-based architecture analysis.
    Returns a dict with keys:
      - project_type (str)
      - languages (list of str)
      - observations (list of str)
      - risk_level (str)
    """
    total_files = len(files_dict)
    if total_files == 0:
        return {
            "project_type": "Unknown Project",
            "languages": ["None detected"],
            "observations": ["No source files detected."],
            "risk_level": "LOW"
        }

    # 1. Detect Languages and Count Extensions
    lang_counts = {}
    ext_mapping = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "React (JS)",
        ".ts": "TypeScript",
        ".tsx": "React (TS)",
        ".java": "Java",
        ".cpp": "C/C++",
        ".c": "C/C++",
        ".html": "HTML",
        ".css": "CSS",
        ".php": "PHP",
        ".go": "Go",
        ".rs": "Rust",
        ".sql": "SQL",
        ".kt": "Kotlin"
    }

    for filename in files_dict.keys():
        _, ext = os.path.splitext(filename.lower())
        if ext in ext_mapping:
            lang = ext_mapping[ext]
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    # Format languages sorted by occurrence
    sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
    detected_languages = [l[0] for l in sorted_langs] if sorted_langs else ["Other"]

    # 2. Check for File Name/Path Patterns (Observations & Layers)
    observations = []
    layers = set()
    manifests_present = False
    has_subfolders = False

    # Track directory hierarchy
    root_files_count = 0

    for filename, content in files_dict.items():
        normalized_path = filename.replace("\\", "/").lower()
        base = normalized_path.split('/')[-1]

        # Check for folder structures (slash in path)
        if '/' in normalized_path:
            has_subfolders = True
        else:
            root_files_count += 1

        # Check for dependency manifests
        if base in ("requirements.txt", "package.json", "package-lock.json", "pom.xml", "build.gradle"):
            manifests_present = True

        # Authentication module detection
        if base in ("auth.py", "authentication.py") or \
           "login" in base or \
           "auth" in normalized_path or \
           any(k in content.lower() for k in ("bcrypt", "jwt.encode", "authenticate(", "login_user", "login_required")):
            layers.add("Authentication")

        # API layer detection
        if base == "api.py" or \
           "routes/" in normalized_path or \
           "controllers/" in normalized_path or \
           re.search(r'from\s+(fastapi|flask|django|express)\s+import', content) or \
           re.search(r'(app\s*=\s*fastapi|app\s*=\s*flask|express\(\))', content):
            layers.add("API")

        # Database layer detection
        if base in ("database.py", "db.py", "models.py") or \
           "database/" in normalized_path or \
           "db/" in normalized_path or \
           any(k in content.lower() for k in ("sqlalchemy", "sqlite3", "psycopg2", "db.model", "pymongo", "mongoose", "sequelize", "prisma")):
            layers.add("Database")

        # Frontend layer detection
        if "frontend/" in normalized_path or \
           "client/" in normalized_path or \
           base.endswith((".html", ".css", ".js", ".jsx", ".ts", ".tsx")):
            layers.add("Frontend")

        # Utility layer detection
        if "utils/" in normalized_path or "helpers/" in normalized_path or \
           base in ("util.py", "utils.py", "helper.py", "helpers.py"):
            layers.add("Utility")

        # Service layer detection
        if "services/" in normalized_path or "service/" in normalized_path or \
           base in ("service.py", "services.py"):
            layers.add("Service")

        # RAG architecture detection
        if "rag/" in normalized_path or \
           any(k in normalized_path or k in content.lower() for k in ("vector_store", "embedding", "retriever", "chroma", "pinecone")):
            layers.add("RAG")

        # Static analysis module detection
        if "static_analysis/" in normalized_path or "bandit" in normalized_path:
            layers.add("StaticAnalysis")

        # Configuration layer detection
        if "config/" in normalized_path or "settings/" in normalized_path or \
           base in (".env", "config.py", "settings.py", "configuration"):
            layers.add("Configuration")

    # Add observations based on layers (in logical order)
    if "API" in layers:
        observations.append("API layer detected.")
    if "Authentication" in layers:
        observations.append("Authentication module detected.")
    if "Database" in layers:
        observations.append("Database layer detected.")
    if "Frontend" in layers:
        observations.append("Frontend layer detected.")
    if "Utility" in layers:
        observations.append("Utility layer detected.")
    if "Service" in layers:
        observations.append("Service layer detected.")
    if "Database" in layers and "Database layer detected." not in observations:
        observations.append("Database layer detected.")
    if "RAG" in layers:
        observations.append("RAG architecture detected.")
    if "StaticAnalysis" in layers:
        observations.append("Static analysis module detected.")
    if "Configuration" in layers:
        observations.append("Configuration management detected.")

    # Deduplicate observations while preserving order
    seen_obs = set()
    deduped_obs = []
    for obs in observations:
        if obs not in seen_obs:
            seen_obs.add(obs)
            deduped_obs.append(obs)
    observations = deduped_obs

    # 3. Project Type Classification
    is_python = "Python" in lang_counts
    is_js_ts = any(k in lang_counts for k in ("JavaScript", "TypeScript", "React (JS)", "React (TS)"))
    is_java = "Java" in lang_counts

    has_streamlit = False
    for content in files_dict.values():
        if "import streamlit" in content or "streamlit" in content:
            has_streamlit = True
            break

    if is_python and has_streamlit:
        project_type = "Streamlit Application"
    elif is_python and is_js_ts:
        project_type = "Full Stack Application"
    elif is_java and len(lang_counts) == 1:
        project_type = "Java Application"
    elif is_python and ("API" in layers or len(lang_counts) == 1):
        project_type = "Backend API Application"
    elif len(lang_counts) > 1:
        project_type = "Mixed Language Project"
    else:
        project_type = "Backend API Application"

    # 4. Architecture Risk Scoring
    root_file_percentage = root_files_count / total_files if total_files > 0 else 0.0
    layers_count = len(layers)
    is_mixed_without_manifests = (len(lang_counts) > 1) and (not manifests_present)

    # HIGH: Monolithic structure, Large project without organization, No identifiable layers
    if layers_count == 0 or (total_files > 5 and not has_subfolders) or (total_files > 5 and root_file_percentage > 0.70):
        risk_level = "HIGH"
    # MEDIUM: Partial architecture issues, Mixed concerns (mixed languages without manifests), Missing layers / >70% root
    elif is_mixed_without_manifests or (total_files > 5 and layers_count == 1) or (root_file_percentage > 0.70):
        risk_level = "MEDIUM"
    # LOW: Clear layered structure (layers >= 2, root <= 70%), Small project with concerns (files <= 5, layers >= 1, subfolders exist)
    elif (layers_count >= 2 and root_file_percentage <= 0.70) or (total_files <= 5 and layers_count >= 1 and has_subfolders):
        risk_level = "LOW"
    else:
        risk_level = "MEDIUM"

    # Fallback to LOW if project has 1 or 2 files
    if total_files <= 2:
        risk_level = "LOW"

    return {
        "project_type": project_type,
        "languages": detected_languages,
        "observations": observations if observations else ["No specific architecture layers detected."],
        "risk_level": risk_level
    }

def generate_architecture_report_section(analysis):
    section = "## Repository Architecture Analysis\n"
    
    section += "\nProject Type:\n"
    section += f"\n* {analysis['project_type']}\n"
    
    section += "\nLanguages:\n"
    for lang in analysis['languages']:
        section += f"\n* {lang}"
    section += "\n"
    
    section += "\nArchitecture Observations:\n"
    for obs in analysis['observations']:
        section += f"\n* {obs}"
    section += "\n"
    
    section += "\nArchitecture Risk:\n"
    section += f"\n* {analysis['risk_level']}"
    
    return section

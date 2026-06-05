import os

SUPPORTED_EXTENSIONS = (
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".html",
    ".css",
    ".php",
    ".go",
    ".rs",
    ".sql",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".kt"
)

MAX_FILE_SIZE_KB = 500
MAX_PROJECT_FILES = 150
MAX_TOTAL_PROJECT_MB = 20

IGNORE_FOLDERS = (
    "node_modules",
    ".git",
    ".github",
    "__pycache__",
    "venv",
    "env",
    "dist",
    "build",
    ".next",
    ".idea",
    ".vscode",
    "coverage",
    "docs",
    "tests",
    "test"
)

def get_project_files(project_path):

    files_data = []
    total_size_bytes = 0
    
    for root, dirs, files in os.walk(project_path):

        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_FOLDERS
        ]

        for file in files:

            if not file.endswith(SUPPORTED_EXTENSIONS) and file != "requirements.txt":
                continue

            file_path = os.path.join(
                root,
                file
            )

            file_size_kb = os.path.getsize(file_path) / 1024

            if file_size_kb > MAX_FILE_SIZE_KB:
                continue
            
            # Project size protection
            file_size = os.path.getsize(file_path)

            total_size_bytes += file_size

            if total_size_bytes > (MAX_TOTAL_PROJECT_MB * 1024 * 1024):
                print(
                    f"Project exceeded {MAX_TOTAL_PROJECT_MB} MB. Stopping scan."
                )
                return files_data

            if len(files_data) >= MAX_PROJECT_FILES:
                print(
                    f"Project exceeded {MAX_PROJECT_FILES} files. Stopping scan."
                )
                return files_data

            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as f:

                    content = f.read()

                    if len(content.strip()) == 0:
                        continue

                    files_data.append({
                    "filename": os.path.relpath(
                        file_path,
                        project_path
                    ),
                    "filepath": file_path,
                    "content": content
                })
            except Exception as e:

                print(
                    f"Error reading {file}: {e}"
                )

    return files_data

def build_lightweight_context(all_files, selected_filenames, project_type):
    import re
    context_str = "Project Structure & Definitions Context:\n"
    context_str += f"- Project Type: {project_type}\n"
    context_str += "- Selected Files for Review:\n"
    for fname in selected_filenames:
        context_str += f"  * {fname}\n"
        
    context_str += "- Definitions in files:\n"
    
    import_pat = re.compile(r'^\s*(?:import\s+([\w\.]+)|from\s+([\w\.]+)\s+import)', re.MULTILINE)
    def_pat = re.compile(r'^\s*(?:def|class)\s+(\w+)', re.MULTILINE)
    
    for f in all_files:
        filename = f["filename"]
        content = f.get("content", "") or ""
        
        if not filename.endswith((".py", ".js", ".ts", ".jsx", ".tsx", ".go")):
            continue
            
        imports = set()
        for m in import_pat.finditer(content):
            val = m.group(1) or m.group(2)
            if val:
                imports.add(val.split('.')[0])
                
        defines = set()
        for m in def_pat.finditer(content):
            val = m.group(1)
            if val:
                defines.add(val)
                
        if defines or imports:
            context_str += f"  * File '{filename}':\n"
            if defines:
                context_str += f"    - Defines: {', '.join(sorted(list(defines)))}\n"
            if imports:
                context_str += f"    - Imports: {', '.join(sorted(list(imports)))}\n"
                
    return context_str
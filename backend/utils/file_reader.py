import os

SUPPORTED_EXTENSIONS = (
    ".py",
    ".js",
    ".java",
    ".cpp",
    ".c",
    ".html",
    ".css"
)

IGNORE_FOLDERS = (
    "node_modules",
    ".git",
    "__pycache__",
    "venv",
    "env",
    "dist",
    "build",
    ".next",
    ".idea",
    ".vscode",
    "coverage"
)

def get_project_files(project_path):

    files_data = []

    for root, dirs, files in os.walk(project_path):

        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_FOLDERS
        ]

        for file in files:

            if not file.endswith(
                SUPPORTED_EXTENSIONS
            ):
                continue

            file_path = os.path.join(
                root,
                file
            )

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
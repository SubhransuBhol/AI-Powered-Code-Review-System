from utils.file_reader import get_project_files

files = get_project_files(
    "../sample_project"
)

print(
    f"Files found: {len(files)}"
)

for file in files:
    print(file["filename"])

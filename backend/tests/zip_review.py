from utils.zip_handler import extract_zip
from file_reader import get_project_files
from review_engine import review_single_file

extract_path = extract_zip(
    "../uploads/sample_project.zip",
    "../uploads/extracted_project"
)

files = get_project_files(extract_path)

for file in files:

    review = review_single_file(
        file["filename"],
        file["content"]
    )

    print(review)
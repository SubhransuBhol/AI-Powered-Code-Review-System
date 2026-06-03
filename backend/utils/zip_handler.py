import zipfile
import os
import shutil

def extract_zip(zip_path, extract_to):

    # Delete old extracted project

    if os.path.exists(extract_to):

        shutil.rmtree(
            extract_to
        )

    # Create fresh folder

    os.makedirs(
        extract_to,
        exist_ok=True
    )

    # Extract ZIP

    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as zip_ref:

        zip_ref.extractall(
            extract_to
        )

    return extract_to
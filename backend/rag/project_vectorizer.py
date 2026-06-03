from utils.file_reader import get_project_files
from rag.embeddings import generate_embedding
from rag.vector_store import store_code

def vectorize_project(project_path):

    files = get_project_files(
        project_path
    )

    count = 0

    for file in files:

        embedding = generate_embedding(
            file["content"]
        )

        store_code(
            file["filename"],
            file["content"],
            embedding
        )

        count += 1

    return count

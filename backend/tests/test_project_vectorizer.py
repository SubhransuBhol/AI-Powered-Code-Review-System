from rag.project_vectorizer import (
    vectorize_project
)

count = vectorize_project(
    "../sample_project"
)

print(
    f"Stored {count} files"
)

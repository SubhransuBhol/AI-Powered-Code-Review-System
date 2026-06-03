from rag.embeddings import generate_embedding
from rag.vector_store import (
    store_code,
    search_code
)

code = """
def add(a,b):
    return a+b
"""

embedding = generate_embedding(
    code
)

store_code(
    "code_1",
    code,
    embedding
)

results = search_code(
    embedding
)

print(results)

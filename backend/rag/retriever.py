from rag.embeddings import generate_embedding
from rag.vector_store import search_code

def retrieve_code(
    query,
    top_k=3
):

    query_embedding = generate_embedding(
        query
    )

    results = search_code(
        query_embedding,
        top_k
    )

    return results

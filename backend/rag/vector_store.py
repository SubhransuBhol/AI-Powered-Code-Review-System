import chromadb

client = chromadb.PersistentClient(
    path="../vector_db"
)

collection = client.get_or_create_collection(
    name="code_reviews"
)

def store_code(
    doc_id,
    content,
    embedding
):

    try:

        collection.delete(
            ids=[doc_id]
        )

    except:
        pass

    collection.add(
        ids=[doc_id],
        documents=[content],
        embeddings=[embedding]
    )

def search_code(
    embedding,
    top_k=3
):

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k
    )

    return results

def clear_collection():

    global collection

    try:
        client.delete_collection(
            "code_reviews"
        )
    except:
        pass

    collection = client.get_or_create_collection(
        name="code_reviews"
    )

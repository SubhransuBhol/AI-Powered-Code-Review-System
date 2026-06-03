from rag.retriever import retrieve_code
from review_engine import review_single_file


def rag_review(query):

    results = retrieve_code(
        query,
        top_k=3
    )

    reviews = ""

    documents = results["documents"][0]
    ids = results["ids"][0]

    for filename, content in zip(
        ids,
        documents
    ):

        review = review_single_file(
            filename,
            content
        )

        reviews += review + "\n\n"

    return reviews

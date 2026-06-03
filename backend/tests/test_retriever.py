from rag.retriever import retrieve_code

results = retrieve_code(
    "authentication login user credentials"
)

print(results)

from rag.embeddings import generate_embedding

print("Generating...")

vector = generate_embedding(
    "def add(a,b): return a+b"
)

print(
    f"Vector Length: {len(vector)}"
)

print(
    vector[:10]
)

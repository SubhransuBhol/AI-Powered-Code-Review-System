print("Loading embeddings.py")

from sentence_transformers import SentenceTransformer

print("Loading model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Model loaded!")

def generate_embedding(text):

    embedding = model.encode(text)

    return embedding.tolist()


from sentence_transformers import SentenceTransformer

model = None

BATCH_SIZE = 50

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_embedding_model():
    global model

    if model is None:
        model = SentenceTransformer(MODEL_NAME)

    return model


def embed_query(query: str):
    """Generate embedding for a single query."""

    model = get_embedding_model()

    embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    return embedding.tolist()


def embed_texts(texts: list[str]):
    """Generate embeddings for multiple texts in batches."""

    model = get_embedding_model()

    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):

        batch = texts[i:i + BATCH_SIZE]

        embeddings = model.encode(
            batch,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        all_embeddings.extend(embeddings.tolist())

    return all_embeddings

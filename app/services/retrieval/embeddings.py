import logfire
from sentence_transformers import SentenceTransformer
from app.config import settings

_model = None


def get_embedding_model() -> SentenceTransformer:
    """
    Lazy initialization of local SentenceTransformer model.
    Runs entirely locally on CPU/GPU without external cloud dependencies.
    """
    global _model
    if _model is None:
        model_name = getattr(settings, "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
        with logfire.span("Initializing Local Embedding Model", model=model_name):
            try:
                _model = SentenceTransformer(model_name, local_files_only=True)
            except Exception:
                _model = SentenceTransformer(model_name)
            logfire.info(f"Loaded local embedding model: {model_name}")
    return _model


def embed_query(query: str) -> list[float]:
    """Embeds a single query string using local sentence-transformers."""
    model = get_embedding_model()
    return model.encode(query).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeds a list of text strings in batches."""
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = model.encode(texts)
    return embeddings.tolist()

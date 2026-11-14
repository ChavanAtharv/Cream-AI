"""Turn text into embedding vectors.

Uses the small ONNX MiniLM model that ships with Chroma. The model is
downloaded the first time it is used (about 80 MB) and then cached.
"""

_embedder = None


def _get_embedder():
    """Create the embedding model once, on first use."""
    global _embedder
    if _embedder is None:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        _embedder = DefaultEmbeddingFunction()
    return _embedder


def embed_texts(texts):
    """Return one vector (a list of floats) for each text."""
    texts = list(texts)
    if not texts:
        return []
    vectors = _get_embedder()(texts)
    return [[float(value) for value in vector] for vector in vectors]

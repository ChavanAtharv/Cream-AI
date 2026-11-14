"""Store chunk embeddings in a persistent Chroma collection and search them.

Build the index from the project root:
    python -m app.vectorstore
"""

from pathlib import Path

import chromadb

from app.chunking import build_chunks
from app.embed import embed_texts

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"
COLLECTION_NAME = "scheme_chunks"
BATCH_SIZE = 64


def get_collection(path=CHROMA_DIR, name=COLLECTION_NAME):
    """Open (or create) the persistent collection."""
    client = chromadb.PersistentClient(path=str(path))
    return client.get_or_create_collection(name=name)


def is_indexed(path=CHROMA_DIR, name=COLLECTION_NAME):
    """True when the collection exists and holds at least one chunk."""
    return get_collection(path, name).count() > 0


def index_chunks(
    chunks, path=CHROMA_DIR, name=COLLECTION_NAME, embed_fn=embed_texts
):
    """Rebuild the collection from scratch with the given chunks.

    Returns the number of chunks stored.
    """
    client = chromadb.PersistentClient(path=str(path))
    try:
        client.delete_collection(name)
    except Exception:  # the collection does not exist yet
        pass
    collection = client.get_or_create_collection(name=name)

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["text"] for chunk in batch],
            embeddings=embed_fn([chunk["text"] for chunk in batch]),
            metadatas=[
                {
                    "title": chunk["title"],
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "file": chunk["file"],
                    "scheme_id": chunk["scheme_id"],
                }
                for chunk in batch
            ],
        )
    return collection.count()


def search(
    query, top_k=5, path=CHROMA_DIR, name=COLLECTION_NAME, embed_fn=embed_texts
):
    """Return the chunks closest in meaning to the query, best first.

    Each hit has: text, title, source, page, file, scheme_id, distance
    (smaller distance means a closer match).
    """
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    if not query.strip() or top_k < 1:
        return []

    collection = get_collection(path, name)
    if collection.count() == 0:
        return []

    result = collection.query(
        query_embeddings=embed_fn([query]),
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for text, meta, distance in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append({"text": text, **meta, "distance": round(float(distance), 4)})
    return hits


def main():
    chunks = build_chunks()
    if not chunks:
        print("No chunks found. Add files to data/documents/ first.")
        return
    count = index_chunks(chunks)
    print(f"Indexed {count} chunks into {CHROMA_DIR}")


if __name__ == "__main__":
    main()

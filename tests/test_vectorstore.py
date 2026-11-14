"""Tests for app.vectorstore and GET /search/semantic (embeddings are faked)."""

import hashlib
import math
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.vectorstore import index_chunks, is_indexed, search

client = TestClient(app)


def fake_embed(texts):
    """Word-hash vectors: texts that share words end up close together."""
    vectors = []
    for text in texts:
        vector = [0.0] * 64
        for word in text.lower().split():
            vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        vectors.append([v / norm for v in vector])
    return vectors


def _chunk(chunk_id, text, title, page=1):
    return {
        "id": chunk_id,
        "text": text,
        "title": title,
        "source": f"https://example.gov.in/{chunk_id}",
        "page": page,
        "file": f"{chunk_id}.pdf",
        "scheme_id": "",
    }


CHUNKS = [
    _chunk("a", "street vendor working capital loan without collateral", "SVANidhi"),
    _chunk("b", "monthly pension after age sixty for workers", "APY", page=2),
    _chunk("c", "income support for small landholding farmer families", "PM-KISAN"),
]


def test_index_and_search_returns_closest_chunk_with_metadata(tmp_path):
    assert index_chunks(CHUNKS, path=tmp_path, embed_fn=fake_embed) == 3
    hits = search("vendor loan", top_k=2, path=tmp_path, embed_fn=fake_embed)
    assert len(hits) == 2
    assert hits[0]["title"] == "SVANidhi"
    assert hits[0]["source"] == "https://example.gov.in/a"
    assert hits[0]["distance"] <= hits[1]["distance"]
    assert hits[1]["page"] in (1, 2)


def test_reindexing_replaces_old_chunks(tmp_path):
    index_chunks(CHUNKS, path=tmp_path, embed_fn=fake_embed)
    assert index_chunks(CHUNKS[:1], path=tmp_path, embed_fn=fake_embed) == 1


def test_search_on_empty_index_or_blank_query_returns_empty(tmp_path):
    assert not is_indexed(path=tmp_path)
    assert search("farmer", path=tmp_path, embed_fn=fake_embed) == []
    index_chunks(CHUNKS, path=tmp_path, embed_fn=fake_embed)
    assert search("   ", path=tmp_path, embed_fn=fake_embed) == []


def test_search_top_k_larger_than_index_is_capped(tmp_path):
    index_chunks(CHUNKS, path=tmp_path, embed_fn=fake_embed)
    assert len(search("farmer", top_k=20, path=tmp_path, embed_fn=fake_embed)) == 3


def test_semantic_endpoint_returns_hits():
    hit = {"text": "t", "title": "T", "source": "s", "page": 1, "distance": 0.1}
    with patch("app.main.is_indexed", return_value=True), patch(
        "app.main.semantic_search", return_value=[hit]
    ):
        response = client.get("/search/semantic", params={"q": "street vendor"})
    assert response.status_code == 200
    assert response.json()[0]["title"] == "T"


def test_semantic_endpoint_without_index_gives_503():
    with patch("app.main.is_indexed", return_value=False):
        response = client.get("/search/semantic", params={"q": "street vendor"})
    assert response.status_code == 503


def test_semantic_endpoint_rejects_missing_query():
    assert client.get("/search/semantic").status_code == 422

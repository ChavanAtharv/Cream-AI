"""Tests for app.smart_search and the FastAPI endpoints in app.main."""

import pytest
from fastapi.testclient import TestClient

from app.main import RECORDS, app
from app.smart_search import SmartSearcher

client = TestClient(app)


# ---- SmartSearcher -------------------------------------------------------

def test_smart_search_ranks_relevant_scheme_first():
    searcher = SmartSearcher(RECORDS)
    results = searcher.search("pension for unorganised workers", top_k=3)
    assert results
    assert "Pension" in results[0][0]["scheme_name"]
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True)


def test_smart_search_unrelated_query_returns_empty():
    assert SmartSearcher(RECORDS).search("zzzqqqxxx") == []


def test_smart_search_blank_query_returns_empty():
    assert SmartSearcher(RECORDS).search("   ") == []


def test_smart_search_rejects_non_string():
    with pytest.raises(TypeError):
        SmartSearcher(RECORDS).search(None)


def test_smart_search_handles_empty_records():
    assert SmartSearcher([]).search("farmer") == []


# ---- API -----------------------------------------------------------------

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_records_respects_limit():
    response = client.get("/records", params={"limit": 3})
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_records_rejects_invalid_limit():
    assert client.get("/records", params={"limit": 0}).status_code == 422


def test_record_by_id_found():
    record_id = RECORDS[0]["id"]
    response = client.get(f"/records/{record_id}")
    assert response.status_code == 200
    assert response.json()["id"] == record_id


def test_record_by_id_missing_returns_404():
    assert client.get("/records/DOES-NOT-EXIST").status_code == 404


def test_search_endpoint_returns_ranked_results():
    response = client.get("/search", params={"q": "farmer income support"})
    assert response.status_code == 200
    body = response.json()
    assert body
    assert {"score", "record"} <= set(body[0])


def test_search_requires_query():
    assert client.get("/search").status_code == 422


def test_questions_returns_matches():
    response = client.post("/questions", json={"question": "I am a street vendor"})
    assert response.status_code == 200
    assert response.json()["matches"]


def test_questions_rejects_short_question():
    assert client.post("/questions", json={"question": "hi"}).status_code == 422

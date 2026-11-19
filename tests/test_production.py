"""Tests for Day 12 production improvements: latency logging, caching, input limits."""

import logging
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.cache import CACHE
from app.llm import complete
from app.main import app

client = TestClient(app)


def test_request_latency_header_present():
    """Verify that requests return the measured latency header X-Process-Time-Ms."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-process-time-ms" in response.headers
    process_time = float(response.headers["x-process-time-ms"])
    assert process_time >= 0.0


def test_api_search_caching_and_stats():
    """Verify that repeated searches result in cache hits and increment cache stats."""
    CACHE.clear()

    # First search -> Cache Miss
    res1 = client.get("/search?q=farmer&limit=3")
    assert res1.status_code == 200
    data1 = res1.json()

    # Second identical search -> Cache Hit
    res2 = client.get("/search?q=farmer&limit=3")
    assert res2.status_code == 200
    assert res2.json() == data1

    stats_res = client.get("/cache/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1
    assert stats["hit_rate"] > 0


def test_input_limits_on_search_and_records():
    """Verify input length restrictions and blank parameter rejections."""
    # Blank query
    assert client.get("/search?q=").status_code == 422
    assert client.get("/search?q=   ").status_code == 422

    # Exceedingly long query (> 500 chars)
    long_q = "kisan " * 105
    assert len(long_q) > 500
    assert client.get(f"/search?q={long_q}").status_code == 422

    # Invalid limits
    assert client.get("/search?q=kisan&limit=0").status_code == 422
    assert client.get("/search?q=kisan&limit=100").status_code == 422


def test_token_usage_logging_when_available(caplog):
    """Verify that LLM token usage metadata is logged without leaking credentials or prompts."""
    fake_response = {
        "choices": [{"message": {"content": "Test answer"}}],
        "usage": {
            "prompt_tokens": 42,
            "completion_tokens": 18,
            "total_tokens": 60,
        },
    }

    with patch("app.llm._post", return_value=fake_response), patch.dict(
        "os.environ",
        {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "secret-key", "GROQ_MODEL": "test-model"},
    ):
        with caplog.at_level(logging.INFO):
            reply = complete("System test prompt", "User test prompt")
            assert reply == "Test answer"

    # Verify log output contains token count, but NOT secrets or full prompt
    log_records = [rec.message for rec in caplog.records if "[TOKEN_USAGE]" in rec.message]
    assert len(log_records) == 1
    log_text = log_records[0]
    assert "prompt_tokens=42" in log_text
    assert "completion_tokens=18" in log_text
    assert "total_tokens=60" in log_text
    assert "secret-key" not in log_text
    assert "System test prompt" not in log_text

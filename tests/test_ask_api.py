"""Tests for POST /ask (the RAG pipeline is faked)."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.chat import ChatParseError
from app.llm import LLMError
from app.main import app

client = TestClient(app)
ANSWER = {"answer": "Yes.", "answerable": True,
          "citations": [{"number": 1, "title": "T", "page": 1, "source": "s", "file": "f"}],
          "closest_distance": 0.5}


def test_ask_returns_answer_and_citations():
    with patch("app.main.is_indexed", return_value=True), patch(
        "app.main.rag_answer", return_value=ANSWER
    ):
        response = client.post("/ask", json={"question": "income tax payer?"})
    assert response.status_code == 200
    assert response.json()["citations"][0]["title"] == "T"


def test_ask_without_index_gives_503():
    with patch("app.main.is_indexed", return_value=False):
        assert client.post("/ask", json={"question": "income tax payer?"}).status_code == 503


def test_ask_provider_and_parse_errors():
    with patch("app.main.is_indexed", return_value=True):
        with patch("app.main.rag_answer", side_effect=LLMError("down")):
            assert client.post("/ask", json={"question": "income tax payer?"}).status_code == 503
        with patch("app.main.rag_answer", side_effect=ChatParseError("bad")):
            assert client.post("/ask", json={"question": "income tax payer?"}).status_code == 502


def test_ask_rejects_bad_input():
    assert client.post("/ask", json={"question": "hi"}).status_code == 422
    assert client.post("/ask", json={"question": "income tax payer?", "top_k": 0}).status_code == 422

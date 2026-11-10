"""Tests for POST /chat (the LLM is always faked)."""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.llm import LLMError
from app.main import app

client = TestClient(app)
GOOD_REPLY = json.dumps(
    {"answer": "Yes.", "confidence": "high", "follow_up": "Anything else?"}
)


def test_chat_returns_structured_json():
    with patch("app.llm.complete", return_value=GOOD_REPLY):
        response = client.post("/chat", json={"question": "street vendor loan"})
    assert response.status_code == 200
    body = response.json()
    assert {"answer", "confidence", "follow_up", "sources"} <= set(body)
    assert body["confidence"] == "high"


def test_chat_unrelated_question_does_not_call_llm():
    with patch("app.llm.complete", side_effect=AssertionError("called")):
        response = client.post("/chat", json={"question": "zzzqqqxxx"})
    assert response.status_code == 200
    assert response.json()["confidence"] == "low"


def test_chat_provider_error_gives_503():
    with patch("app.llm.complete", side_effect=LLMError("key missing")):
        response = client.post("/chat", json={"question": "street vendor loan"})
    assert response.status_code == 503


def test_chat_unreadable_model_reply_gives_502():
    with patch("app.llm.complete", return_value="not json at all"):
        response = client.post("/chat", json={"question": "street vendor loan"})
    assert response.status_code == 502


def test_chat_rejects_bad_input():
    assert client.post("/chat", json={"question": "hi"}).status_code == 422
    body = {"question": "street vendor loan", "prompt_version": "v9"}
    assert client.post("/chat", json=body).status_code == 422

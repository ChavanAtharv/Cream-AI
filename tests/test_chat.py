"""Tests for app.chat and app.llm (no real network calls)."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from app import llm
from app.chat import (
    NO_MATCH_ANSWER,
    ChatParseError,
    answer_question,
    build_context,
    parse_llm_json,
)
from app.smart_search import SmartSearcher

RECORDS = [
    {
        "id": "SS001",
        "scheme_name": "Atal Pension Yojana (APY)",
        "ministry": "Ministry of Finance",
        "benefit": "Guaranteed monthly pension after age 60.",
        "eligibility": "Indian citizen aged 18 to 40 with a savings bank account.",
        "documents_required": ["Aadhaar", "Bank account details"],
        "source_url": "https://www.myscheme.gov.in/schemes/apy",
    },
    {
        "id": "SS002",
        "scheme_name": "PM Kisan Samman Nidhi",
        "ministry": None,
        "benefit": "Income support for landholding farmers.",
        "eligibility": "Landholding farmer families.",
        "documents_required": [],
        "source_url": "https://www.myscheme.gov.in/schemes/pm-kisan",
    },
]
GOOD_REPLY = json.dumps(
    {"answer": "Yes, APY fits.", "confidence": "high", "follow_up": "Documents?"}
)


# ---- parse_llm_json ------------------------------------------------------

def test_parse_plain_json():
    result = parse_llm_json(GOOD_REPLY)
    assert result == {
        "answer": "Yes, APY fits.",
        "confidence": "high",
        "follow_up": "Documents?",
    }


def test_parse_json_inside_code_fence():
    assert parse_llm_json(f"```json\n{GOOD_REPLY}\n```")["confidence"] == "high"


def test_parse_json_with_extra_text():
    assert parse_llm_json(f"Here you go: {GOOD_REPLY} Hope it helps")["answer"]


def test_parse_unknown_confidence_becomes_low():
    reply = json.dumps({"answer": "ok", "confidence": "certain"})
    assert parse_llm_json(reply)["confidence"] == "low"
    assert parse_llm_json(reply)["follow_up"] == ""


def test_parse_rejects_bad_replies():
    for bad in ["no json here", "{broken", '{"confidence": "high"}', '{"answer": ""}', None]:
        with pytest.raises(ChatParseError):
            parse_llm_json(bad)


# ---- build_context -------------------------------------------------------

def test_build_context_handles_missing_fields():
    text = build_context(RECORDS)
    assert "Scheme: Atal Pension Yojana (APY)" in text
    assert "Documents: Aadhaar; Bank account details" in text
    assert "Ministry: Not available" in text
    assert "Documents: Not specified" in text


# ---- answer_question -----------------------------------------------------

def test_no_match_skips_the_llm():
    def must_not_run(system, task):
        raise AssertionError("LLM should not be called")

    result = answer_question(
        "zzzqqq", SmartSearcher(RECORDS), complete_fn=must_not_run
    )
    assert result["answer"] == NO_MATCH_ANSWER
    assert result["confidence"] == "low"
    assert result["sources"] == []


def test_prompt_contains_question_and_retrieved_scheme():
    seen = {}

    def fake(system, task):
        seen["system"], seen["task"] = system, task
        return GOOD_REPLY

    result = answer_question(
        "pension at age 25", SmartSearcher(RECORDS), complete_fn=fake
    )
    assert "SchemeSaathi" in seen["system"]
    assert "pension at age 25" in seen["task"]
    assert "Atal Pension Yojana" in seen["task"]
    assert result["sources"][0] == "https://www.myscheme.gov.in/schemes/apy"


def test_unknown_prompt_version_is_rejected():
    with pytest.raises(ValueError):
        answer_question("pension", SmartSearcher(RECORDS), version="v9")


# ---- llm.complete --------------------------------------------------------

def _http_reply(payload):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_groq_reply_is_parsed():
    env = {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "k", "GROQ_MODEL": "m"}
    payload = {"choices": [{"message": {"content": "hello"}}]}
    with patch.dict(os.environ, env), patch(
        "app.llm.requests.post", return_value=_http_reply(payload)
    ) as post:
        assert llm.complete("sys", "user") == "hello"
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer k"
    assert post.call_args.kwargs["timeout"] == llm.TIMEOUT_SECONDS


def test_gemini_reply_is_parsed():
    env = {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "k", "GEMINI_MODEL": "m"}
    payload = {"candidates": [{"content": {"parts": [{"text": "hi"}]}}]}
    with patch.dict(os.environ, env), patch(
        "app.llm.requests.post", return_value=_http_reply(payload)
    ):
        assert llm.complete("sys", "user") == "hi"


def test_missing_key_unknown_provider_and_bad_shape():
    with patch.dict(os.environ, {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "", "GROQ_MODEL": "m"}):
        with pytest.raises(llm.LLMError):
            llm.complete("s", "u")
    with patch.dict(os.environ, {"LLM_PROVIDER": "nope"}):
        with pytest.raises(llm.LLMError):
            llm.complete("s", "u")
    env = {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "k", "GROQ_MODEL": "m"}
    with patch.dict(os.environ, env), patch(
        "app.llm.requests.post", return_value=_http_reply({"unexpected": 1})
    ):
        with pytest.raises(llm.LLMError):
            llm.complete("s", "u")


def test_timeout_becomes_llm_error():
    env = {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "k", "GROQ_MODEL": "m"}
    with patch.dict(os.environ, env), patch(
        "app.llm.requests.post", side_effect=requests.exceptions.Timeout()
    ):
        with pytest.raises(llm.LLMError):
            llm.complete("s", "u")


def test_http_error_includes_the_providers_reason_but_not_the_key():
    env = {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "secret-key", "GROQ_MODEL": "m"}
    response = MagicMock(status_code=400)
    response.json.return_value = {"error": {"message": "model not available"}}
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)
    with patch.dict(os.environ, env), patch("app.llm.requests.post", return_value=response):
        with pytest.raises(llm.LLMError) as info:
            llm.complete("s", "u")
    assert "HTTP 400" in str(info.value)
    assert "model not available" in str(info.value)
    assert "secret-key" not in str(info.value)


def test_http_error_without_a_readable_body_still_reports_the_status():
    env = {"LLM_PROVIDER": "groq", "GROQ_API_KEY": "k", "GROQ_MODEL": "m"}
    response = MagicMock(status_code=500)
    response.json.side_effect = ValueError("not json")
    response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)
    with patch.dict(os.environ, env), patch("app.llm.requests.post", return_value=response):
        with pytest.raises(llm.LLMError) as info:
            llm.complete("s", "u")
    assert str(info.value) == "The LLM provider returned HTTP 500"


TOOL_ERROR = "The LLM provider returned HTTP 400: Tool choice is none, but model called a tool"


def test_complete_retries_when_the_model_tries_to_call_a_tool():
    calls = []

    def flaky(system, user, temperature):
        calls.append(1)
        if len(calls) < 3:
            raise llm.LLMError(TOOL_ERROR)
        return "fine"

    with patch.dict(os.environ, {"LLM_PROVIDER": "groq"}), patch.dict(llm.PROVIDERS, {"groq": flaky}):
        assert llm.complete("s", "u") == "fine"
    assert len(calls) == 3


def test_complete_gives_up_after_three_tool_call_errors():
    calls = []

    def always(system, user, temperature):
        calls.append(1)
        raise llm.LLMError(TOOL_ERROR)

    with patch.dict(os.environ, {"LLM_PROVIDER": "groq"}), patch.dict(llm.PROVIDERS, {"groq": always}):
        with pytest.raises(llm.LLMError):
            llm.complete("s", "u")
    assert len(calls) == 3


def test_complete_does_not_retry_other_errors():
    calls = []

    def bad_key(system, user, temperature):
        calls.append(1)
        raise llm.LLMError("The LLM provider returned HTTP 401")

    with patch.dict(os.environ, {"LLM_PROVIDER": "groq"}), patch.dict(llm.PROVIDERS, {"groq": bad_key}):
        with pytest.raises(llm.LLMError):
            llm.complete("s", "u")
    assert len(calls) == 1

"""Tests for app.rag and eval.run_eval.check_result (LLM and search are faked)."""

import json
from unittest.mock import patch

import pytest

from app.chat import ChatParseError
from app.llm import LLMError
from app.rag import (
    IDK_NO_SOURCES,
    IDK_UNSUPPORTED,
    answer_question,
    extract_json,
    format_sources,
)
from eval import run_eval
from eval.run_eval import ask_with_retry, check_result, normalise


def _hit(title, page, distance, file="pm_kisan_faq.pdf"):
    return {
        "text": f"text of {title}",
        "title": title,
        "page": page,
        "source": f"https://example.gov.in/{file}",
        "file": file,
        "scheme_id": "X",
        "distance": distance,
    }


HITS = [_hit("PM-KISAN FAQ", 2, 0.6), _hit("PM-KISAN Guidelines", 3, 0.7, "pm_kisan_og.pdf")]


def _search(hits):
    return lambda question, top_k, path, name: hits


def _complete(reply):
    return lambda system, task: reply


def _ask(reply, hits=HITS, **kwargs):
    return answer_question(
        "income tax payer?", search_fn=_search(hits), complete_fn=_complete(reply), **kwargs
    )


GOOD = json.dumps({"answer": "No, income tax payers are excluded.", "can_answer": True, "citations": [1, 2]})


def test_answer_maps_citation_numbers_to_real_sources():
    result = _ask(GOOD)
    assert result["answerable"] is True
    assert [c["title"] for c in result["citations"]] == ["PM-KISAN FAQ", "PM-KISAN Guidelines"]
    assert result["citations"][0]["page"] == 2
    assert result["citations"][0]["source"].startswith("https://example.gov.in")
    assert result["closest_distance"] == 0.6


def test_invalid_and_duplicate_citation_numbers_are_ignored():
    reply = json.dumps({"answer": "ok", "can_answer": True, "citations": [9, 1, 1, "2", True]})
    result = _ask(reply)
    assert [c["number"] for c in result["citations"]] == [1]


def test_all_hits_too_far_skips_the_llm():
    def must_not_run(system, task):
        raise AssertionError("LLM should not be called")

    far = [_hit("Far", 1, 1.5)]
    result = answer_question("zzzz", search_fn=_search(far), complete_fn=must_not_run)
    assert result["answerable"] is False
    assert result["answer"] == IDK_NO_SOURCES
    assert result["closest_distance"] == 1.5


def test_no_hits_at_all_is_dont_know():
    result = _ask(GOOD, hits=[])
    assert result["answerable"] is False
    assert result["closest_distance"] is None


def test_model_saying_it_cannot_answer_is_respected():
    reply = json.dumps({"answer": "I don't know. The sources cover benefits.", "can_answer": False, "citations": []})
    result = _ask(reply)
    assert result["answerable"] is False
    assert result["citations"] == []
    assert result["answer"].startswith("I don't know")


def test_answer_without_a_valid_citation_is_rejected():
    reply = json.dumps({"answer": "Yes, definitely.", "can_answer": True, "citations": []})
    result = _ask(reply)
    assert result["answerable"] is False
    assert result["answer"] == IDK_UNSUPPORTED


def test_unreadable_replies_raise():
    for bad in ["no json", "{broken", '{"can_answer": true}', '{"answer": "x"}',
                '{"answer": "x", "can_answer": "yes"}']:
        with pytest.raises(ChatParseError):
            _ask(bad)


def test_prompt_has_numbered_sources_and_question():
    seen = {}

    def spy(system, task):
        seen["system"], seen["task"] = system, task
        return GOOD

    answer_question("my question", search_fn=_search(HITS), complete_fn=spy)
    assert "[1] (PM-KISAN FAQ, page 2)" in seen["task"]
    assert "[2] (PM-KISAN Guidelines, page 3)" in seen["task"]
    assert "my question" in seen["task"]
    assert "numbered sources" in seen["system"]


def test_extract_json_and_format_sources():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert format_sources([_hit("T", 4, 0.1)]).startswith("[1] (T, page 4)")


# ---- eval.run_eval.check_result -----------------------------------------

def _result(answerable, answer="ok", file="pm_kisan_faq.pdf"):
    citations = [{"file": file}] if answerable else []
    return {"answerable": answerable, "answer": answer, "citations": citations}


def test_check_result_passes_correct_answer():
    item = {"answerable": True, "expect_file_prefixes": ["pm_kisan_"], "must_mention_any": ["6000"]}
    checks = check_result(item, _result(True, "It is Rs 6000 a year."))
    assert checks["passed"] is True


def test_check_result_flags_wrong_source_and_missing_fact():
    item = {"answerable": True, "expect_file_prefixes": ["apy_"], "must_mention_any": ["6000"]}
    checks = check_result(item, _result(True, "something else"))
    assert checks["source_ok"] is False
    assert checks["mention_ok"] is False
    assert checks["passed"] is False


def test_check_result_unanswerable_needs_dont_know():
    item = {"answerable": False}
    assert check_result(item, _result(False))["passed"] is True
    assert check_result(item, _result(True))["passed"] is False


# ---- eval.run_eval.ask_with_retry ---------------------------------------

CONFIG = {"top_k": 2, "max_distance": 1.0}


def test_ask_with_retry_waits_after_rate_limit():
    calls = []

    def fake(question, **kwargs):
        calls.append(question)
        if len(calls) == 1:
            raise LLMError("The LLM provider returned HTTP 429")
        return {"answerable": True}

    with patch("eval.run_eval.rag.answer_question", side_effect=fake), patch(
        "eval.run_eval.time.sleep"
    ) as sleep:
        assert ask_with_retry("q", CONFIG, "eval_a") == {"answerable": True}
    assert len(calls) == 2
    sleep.assert_called_once()


def test_ask_with_retry_does_not_retry_other_errors():
    with patch(
        "eval.run_eval.rag.answer_question",
        side_effect=LLMError("The LLM provider returned HTTP 404"),
    ) as fake, patch("eval.run_eval.time.sleep"):
        with pytest.raises(LLMError):
            ask_with_retry("q", CONFIG, "eval_a")
    assert fake.call_count == 1


def test_ask_with_retry_gives_up_after_three_rate_limits():
    with patch(
        "eval.run_eval.rag.answer_question",
        side_effect=LLMError("The LLM provider returned HTTP 429"),
    ) as fake, patch("eval.run_eval.time.sleep"):
        with pytest.raises(LLMError):
            ask_with_retry("q", CONFIG, "eval_a")
    assert fake.call_count == 3


# ---- eval.run_eval.write_results ----------------------------------------

def test_write_results_includes_full_text_of_failed_answers(tmp_path):
    config = {"name": "A", "chunk_words": 150, "overlap": 30, "top_k": 4, "max_distance": 1.2}
    item = {"id": 1, "question": "Q?", "answerable": True,
            "expect_file_prefixes": ["x_"], "must_mention_any": []}
    result = {"answer": "A long answer that would be cut in the table. " * 5,
              "answerable": True, "citations": [{"file": "y.pdf"}], "closest_distance": 0.5}
    row = {"item": item, "result": result, "checks": check_result(item, result)}
    run = {"config": config, "chunks": 3, "rows": [row]}

    target = tmp_path / "eval_results.md"
    with patch.object(run_eval, "RESULTS_FILE", target):
        run_eval.write_results([run])

    text = target.read_text(encoding="utf-8")
    assert "Failed answers in full: config A" in text
    assert result["answer"].strip() in text.replace("> ", "")
    assert "Winner: A" in text


def test_key_fact_check_ignores_unicode_spaces_and_hyphens():
    item = {"answerable": True, "expect_file_prefixes": [], "must_mention_any": ["2 lakh", "income-tax"]}
    assert check_result(item, _result(True, "Cover is Rs.\u00a02\u202flakh."))["mention_ok"]
    assert check_result(item, _result(True, "An income\u2011tax payer"))["mention_ok"]
    assert not check_result(item, _result(True, "Cover is Rs. 3 lakh"))["mention_ok"]
    assert normalise("PM\u2011KISAN  Rs.\u00a06000") == "pm-kisan rs. 6000"

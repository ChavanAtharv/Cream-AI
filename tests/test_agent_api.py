"""Tests for POST /agent (the graph is faked)."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.chat import ChatParseError
from app.llm import LLMError
from app.main import app

client = TestClient(app)
DONE = {"status": "done", "thread_id": "t", "answer": "ok", "steps": []}


def post(body, pending=False, **run_kwargs):
    with patch("app.graph.get_graph", return_value="G"), patch(
        "app.graph.has_pending", return_value=pending
    ), patch("app.graph.run_turn", **run_kwargs) as run:
        response = client.post("/agent", json=body)
    return response, run


def test_new_question_runs_a_turn_and_creates_a_thread_id():
    response, run = post({"question": "compare APY and PM-KISAN"}, return_value=DONE)
    assert response.status_code == 200
    kwargs = run.call_args.kwargs
    assert kwargs["question"] == "compare APY and PM-KISAN"
    assert len(run.call_args.args[1]) == 32  # generated thread id


def test_approval_resumes_the_given_thread():
    response, run = post({"thread_id": "abc", "approve": True}, pending=True, return_value=DONE)
    assert response.status_code == 200
    assert run.call_args.args[1] == "abc"
    assert run.call_args.kwargs["approve"] is True


def test_conflicts_between_pending_state_and_request():
    response, _ = post({"thread_id": "abc", "question": "new question"}, pending=True, return_value=DONE)
    assert response.status_code == 409
    response, _ = post({"thread_id": "abc", "approve": True}, pending=False, return_value=DONE)
    assert response.status_code == 409


def test_bad_requests_are_rejected():
    assert client.post("/agent", json={}).status_code == 422
    assert client.post("/agent", json={"question": "hello there", "approve": True}).status_code == 422
    assert client.post("/agent", json={"approve": True}).status_code == 422  # no thread_id
    assert client.post("/agent", json={"question": "hi"}).status_code == 422  # too short


def test_provider_and_parse_errors():
    response, _ = post({"question": "hello there"}, side_effect=LLMError("down"))
    assert response.status_code == 503
    response, _ = post({"question": "hello there"}, side_effect=ChatParseError("bad"))
    assert response.status_code == 502

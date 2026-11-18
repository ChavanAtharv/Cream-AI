"""Tests for app.agent_loop (the LLM and the tools are faked)."""

import json

import pytest

from app.agent_loop import (
    GIVE_UP_ANSWER,
    MAX_STEPS,
    build_system_prompt,
    parse_action,
    run_agent,
    run_tool,
)
from app.chat import ChatParseError
from app.tools import ToolError


def scripted(*replies):
    """A fake LLM that returns the given replies in order and records prompts."""
    calls = []
    queue = list(replies)

    def complete(system, user):
        calls.append(user)
        return queue.pop(0) if len(queue) > 1 else queue[0]

    complete.calls = calls
    return complete


def act(**kwargs):
    return json.dumps(kwargs)


FINAL = act(action="final", answer="Done.")


# ---- parse_action --------------------------------------------------------

def test_parse_action_accepts_the_three_action_types():
    assert parse_action(FINAL) == {"action": "final", "answer": "Done."}
    assert parse_action(act(action="ask_documents", input=" q? ")) == {"action": "ask_documents", "input": "q?"}
    assert parse_action(f"```json\n{act(action='compare_schemes', input=['A', 'B'])}\n```")["input"] == ["A", "B"]


def test_parse_action_rejects_bad_actions():
    bad_replies = [
        "no json",
        act(action="launch_rocket"),
        act(action="final"),
        act(action="ask_documents", input=""),
        act(action="compare_schemes", input="A and B"),
        act(action="compare_schemes", input=["A", 2]),
    ]
    for reply in bad_replies:
        with pytest.raises(ChatParseError):
            parse_action(reply)


# ---- run_tool ------------------------------------------------------------

def test_run_tool_returns_output_and_turns_tool_errors_into_text():
    ok = run_tool({"action": "ask_documents", "input": "q"}, tools={"ask_documents": lambda q: "answer"})
    assert ok == "answer"

    def broken(names):
        raise ToolError("no such scheme")

    text = run_tool({"action": "compare_schemes", "input": ["A", "B"]}, tools={"compare_schemes": broken})
    assert text == "Tool error: no such scheme"


def test_run_tool_truncates_long_output_and_handles_invalid():
    long = run_tool({"action": "ask_documents", "input": "q"}, tools={"ask_documents": lambda q: "x" * 10000})
    assert len(long) == 3000
    assert run_tool({"action": "invalid", "message": "try again"}) == "try again"


# ---- run_agent -----------------------------------------------------------

def test_agent_can_finish_without_tools():
    result = run_agent("hello", complete_fn=scripted(FINAL))
    assert result == {"answer": "Done.", "steps": [], "finished": True}


def test_agent_uses_a_tool_then_answers_with_its_result():
    llm = scripted(act(action="ask_documents", input="annual benefit?"), act(action="final", answer="It is Rs 6000."))
    result = run_agent("benefit?", complete_fn=llm, tools={"ask_documents": lambda q: "Rs 6000 per year"})
    assert result["finished"] is True
    assert result["steps"] == [{"action": "ask_documents", "input": "annual benefit?", "observation": "Rs 6000 per year"}]
    assert "Rs 6000 per year" in llm.calls[1]  # the model saw the tool result


def test_agent_recovers_from_an_unusable_reply():
    llm = scripted("not json at all", FINAL)
    result = run_agent("hi", complete_fn=llm)
    assert result["answer"] == "Done."
    assert result["steps"][0]["action"] == "invalid"
    assert "not usable" in llm.calls[1]


def test_agent_stops_after_max_steps():
    llm = scripted(act(action="ask_documents", input="again"))
    result = run_agent("loop", complete_fn=llm, tools={"ask_documents": lambda q: "same"})
    assert result["finished"] is False
    assert result["answer"] == GIVE_UP_ANSWER
    assert len(result["steps"]) == MAX_STEPS


def test_agent_prompt_includes_conversation_history():
    llm = scripted(FINAL)
    history = [{"question": "What is APY?", "answer": "A pension scheme."}]
    run_agent("and its age limit?", history=history, complete_fn=llm)
    assert "User: What is APY?" in llm.calls[0]
    assert "Assistant: A pension scheme." in llm.calls[0]
    assert "Question: and its age limit?" in llm.calls[0]


def test_system_prompt_lists_both_tools():
    prompt = build_system_prompt()
    assert "ask_documents" in prompt and "compare_schemes" in prompt
    assert "{tools}" not in prompt and "{schemes}" not in prompt

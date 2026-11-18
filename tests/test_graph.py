"""Tests for app.graph (needs langgraph; the LLM and the tools are faked)."""

import json

from app.graph import build_graph, has_pending, is_approved, run_turn


def scripted(*replies):
    queue = list(replies)

    def complete(system, user):
        complete.prompts.append(user)
        return queue.pop(0) if len(queue) > 1 else queue[0]

    complete.prompts = []
    return complete


def act(**kwargs):
    return json.dumps(kwargs)


TOOL_CALL = act(action="ask_documents", input="annual benefit?")
FINAL = act(action="final", answer="It is Rs 6000.")
TOOLS = {"ask_documents": lambda q: "Rs 6000 per year", "compare_schemes": lambda n: "| table |"}


def make(*replies):
    llm = scripted(*replies)
    return build_graph(complete_fn=llm, tools=TOOLS), llm


def test_is_approved():
    assert is_approved(True) and is_approved("Yes") and is_approved(" approve ")
    assert not is_approved(False) and not is_approved("no") and not is_approved(None)


def test_question_without_tools_finishes_straight_away():
    graph, _ = make(FINAL)
    result = run_turn(graph, "t1", question="hello")
    assert result["status"] == "done"
    assert result["answer"] == "It is Rs 6000."
    assert result["steps"] == []


def test_tool_call_pauses_for_approval_then_runs_after_yes():
    graph, llm = make(TOOL_CALL, FINAL)
    first = run_turn(graph, "t2", question="PM-KISAN benefit?")
    assert first["status"] == "awaiting_approval"
    assert first["pending"]["tool"] == "ask_documents"
    assert first["pending"]["input"] == "annual benefit?"
    assert has_pending(graph, "t2")

    second = run_turn(graph, "t2", approve=True)
    assert second["status"] == "done"
    assert second["answer"] == "It is Rs 6000."
    assert second["steps"][0]["observation"] == "Rs 6000 per year"
    assert "Rs 6000 per year" in llm.prompts[1]
    assert not has_pending(graph, "t2")


def test_rejected_tool_is_not_run():
    ran = []
    llm = scripted(TOOL_CALL, FINAL)
    graph = build_graph(complete_fn=llm, tools={"ask_documents": lambda q: ran.append(q) or "x"})
    run_turn(graph, "t3", question="benefit?")
    result = run_turn(graph, "t3", approve=False)
    assert result["status"] == "done"
    assert "did not run" in result["answer"]
    assert ran == []


def test_auto_approve_skips_the_pause():
    graph, _ = make(TOOL_CALL, FINAL)
    result = run_turn(graph, "t4", question="benefit?", auto_approve=True)
    assert result["status"] == "done"
    assert len(result["steps"]) == 1


def test_memory_carries_over_to_the_next_question_on_the_same_thread():
    graph, llm = make(FINAL)
    run_turn(graph, "t5", question="What is APY?")
    run_turn(graph, "t5", question="and who can join it?")
    assert "User: What is APY?" in llm.prompts[1]
    assert "Assistant: It is Rs 6000." in llm.prompts[1]


def test_threads_do_not_share_memory():
    graph, llm = make(FINAL)
    run_turn(graph, "t6a", question="What is APY?")
    run_turn(graph, "t6b", question="something else")
    assert "What is APY?" not in llm.prompts[1]


def test_looping_agent_gives_up_instead_of_running_forever():
    graph, _ = make(TOOL_CALL)
    result = run_turn(graph, "t7", question="loop", auto_approve=True)
    assert result["status"] == "done"
    assert "could not finish" in result["answer"]

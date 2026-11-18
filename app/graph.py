"""The agent rebuilt as a LangGraph graph, with memory and an approval step.

Flow:  decide -> approval -> tools -> decide ... -> finish
- decide:   the LLM picks a tool or finishes (same logic as agent_loop).
- approval: pauses the graph and waits for a yes/no before any tool runs.
- Memory:   a checkpointer stores the conversation per thread_id, so a later
            question on the same thread can refer to earlier ones.
Memory is kept in the server's RAM, so it is lost when the server restarts.
"""

from typing import TypedDict

from app import agent_loop

MAX_HISTORY_TURNS = 10
APPROVE_WORDS = {"yes", "y", "ok", "approve", "approved", "true"}
REJECTED_ANSWER = (
    "Okay, I did not run that step, so I cannot answer the question."
)


class AgentState(TypedDict, total=False):
    question: str
    history: list  # [{"question", "answer"}], kept across turns
    steps: list
    action: dict
    approved: bool
    answer: str
    finished: bool


def is_approved(decision):
    """Turn whatever the human sent back into True or False."""
    if isinstance(decision, bool):
        return decision
    return str(decision).strip().lower() in APPROVE_WORDS


def build_graph(checkpointer=None, complete_fn=None, tools=None):
    """Create and compile the graph. complete_fn and tools can be faked."""
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import interrupt

    def decide(state):
        action = agent_loop.next_action(
            state["question"],
            state.get("steps", []),
            state.get("history", []),
            complete_fn,
        )
        return {"action": action}

    def route_after_decide(state):
        action = state["action"]
        if action["action"] == "final":
            return "finish"
        if len(state.get("steps", [])) >= agent_loop.MAX_STEPS:
            return "give_up"
        if action["action"] == "invalid":
            return "tools"  # nothing to approve, just tell the model
        return "approval"

    def approval(state):
        # On resume LangGraph runs this node again from the top, so it must
        # not do anything except ask.
        action = state["action"]
        decision = interrupt(
            {
                "tool": action["action"],
                "input": action["input"],
                "message": "Do you approve running this tool?",
            }
        )
        return {"approved": is_approved(decision)}

    def route_after_approval(state):
        return "tools" if state["approved"] else "rejected"

    def tools_node(state):
        observation = agent_loop.run_tool(state["action"], tools)
        step = agent_loop.make_step(state["action"], observation)
        return {"steps": state.get("steps", []) + [step]}

    def rejected(state):
        return {"answer": REJECTED_ANSWER}

    def give_up(state):
        return {"answer": agent_loop.GIVE_UP_ANSWER}

    def finish(state):
        answer = state.get("answer") or state["action"].get("answer", "")
        turn = {"question": state["question"], "answer": answer}
        history = (state.get("history", []) + [turn])[-MAX_HISTORY_TURNS:]
        return {"answer": answer, "finished": True, "history": history}

    builder = StateGraph(AgentState)
    builder.add_node("decide", decide)
    builder.add_node("approval", approval)
    builder.add_node("tools", tools_node)
    builder.add_node("rejected", rejected)
    builder.add_node("give_up", give_up)
    builder.add_node("finish", finish)

    builder.add_edge(START, "decide")
    builder.add_conditional_edges(
        "decide",
        route_after_decide,
        {"finish": "finish", "give_up": "give_up", "tools": "tools", "approval": "approval"},
    )
    builder.add_conditional_edges(
        "approval", route_after_approval, {"tools": "tools", "rejected": "rejected"}
    )
    builder.add_edge("tools", "decide")
    builder.add_edge("rejected", "finish")
    builder.add_edge("give_up", "finish")
    builder.add_edge("finish", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())


_graph = None


def get_graph():
    """One shared graph (and one shared memory) for the running server."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def _config(thread_id):
    return {"configurable": {"thread_id": thread_id}}


def has_pending(graph, thread_id):
    """True when this thread is paused, waiting for an approval."""
    return bool(graph.get_state(_config(thread_id)).next)


def _fresh_input(question):
    # history is not listed here, so it is kept from earlier turns.
    return {
        "question": question,
        "steps": [],
        "action": {},
        "approved": False,
        "answer": "",
        "finished": False,
    }


def format_result(thread_id, result):
    interrupts = result.get("__interrupt__")
    if interrupts:
        first = interrupts[0]
        return {
            "status": "awaiting_approval",
            "thread_id": thread_id,
            "pending": getattr(first, "value", first),
        }
    return {
        "status": "done",
        "thread_id": thread_id,
        "answer": result.get("answer", ""),
        "steps": result.get("steps", []),
    }


def run_turn(graph, thread_id, question=None, approve=None, auto_approve=False):
    """Start a new turn (question) or answer a pending approval (approve)."""
    from langgraph.types import Command

    config = _config(thread_id)
    if question is not None:
        result = graph.invoke(_fresh_input(question), config)
    else:
        result = graph.invoke(Command(resume=approve), config)
    while auto_approve and result.get("__interrupt__"):
        result = graph.invoke(Command(resume=True), config)
    return format_result(thread_id, result)

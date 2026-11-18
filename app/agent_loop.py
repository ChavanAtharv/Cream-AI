"""A hand-written agent: the LLM picks a tool or finishes, we run the tool.

Each turn the model replies with one JSON action:
    {"action": "ask_documents", "input": "question"}
    {"action": "compare_schemes", "input": ["Scheme A", "Scheme B"]}
    {"action": "final", "answer": "..."}
We run the tool, show the model what it returned, and repeat until the
model finishes or MAX_STEPS tool calls have been used.
"""

from app import llm
from app.chat import ChatParseError, load_prompt
from app.rag import extract_json
from app.tools import TOOL_DESCRIPTIONS, TOOLS, ToolError, load_scheme_records

MAX_STEPS = 4
MAX_OBSERVATION_CHARS = 3000
HISTORY_TURNS = 3

GIVE_UP_ANSWER = (
    "I could not finish this within the allowed number of steps, so I do not "
    "have a reliable answer."
)


def scheme_names():
    """Names of the schemes the compare tool knows (empty if unreadable)."""
    try:
        return [record["scheme_name"] for record in load_scheme_records()]
    except (ToolError, KeyError):
        return []


def build_system_prompt():
    tools = "\n".join(f"- {name}: {text}" for name, text in TOOL_DESCRIPTIONS.items())
    schemes = "\n".join(f"- {name}" for name in scheme_names()) or "(none loaded)"
    return (
        load_prompt("agent_system")
        .replace("{tools}", tools)
        .replace("{schemes}", schemes)
    )


def format_history(history):
    """Earlier turns of the conversation (the agent's short-term memory)."""
    turns = (history or [])[-HISTORY_TURNS:]
    if not turns:
        return ""
    lines = ["Earlier in this conversation:"]
    for turn in turns:
        lines.append(f"User: {turn['question']}")
        lines.append(f"Assistant: {turn['answer']}")
    return "\n".join(lines) + "\n\n"


def format_steps(steps):
    if not steps:
        return ""
    lines = ["Steps so far:"]
    for number, step in enumerate(steps, start=1):
        lines.append(f"Step {number}: {step['action']} with input {step['input']}")
        lines.append(f"Result: {step['observation']}")
    return "\n".join(lines) + "\n\n"


def parse_action(text):
    """Turn the model's reply into a validated action dict."""
    data = extract_json(text)
    action = data.get("action")

    if action == "final":
        answer = data.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            raise ChatParseError("final action has no answer")
        return {"action": "final", "answer": answer.strip()}

    if action == "ask_documents":
        value = data.get("input")
        if not isinstance(value, str) or not value.strip():
            raise ChatParseError("ask_documents needs a text input")
        return {"action": action, "input": value.strip()}

    if action == "compare_schemes":
        value = data.get("input")
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise ChatParseError("compare_schemes needs a list of names")
        return {"action": action, "input": value}

    raise ChatParseError(f"unknown action {action!r}")


def next_action(question, steps, history=None, complete_fn=None):
    """Ask the model what to do next; bad replies become an 'invalid' action."""
    user_prompt = (
        format_history(history)
        + f"Question: {question}\n\n"
        + format_steps(steps)
        + "What is your next action? Reply with one JSON object only."
    )
    raw = (complete_fn or llm.complete)(build_system_prompt(), user_prompt)
    try:
        return parse_action(raw)
    except ChatParseError as error:
        return {
            "action": "invalid",
            "message": f"Your last reply was not usable ({error}). "
            "Reply with one JSON object in the format described.",
        }


def run_tool(action, tools=None):
    """Run the chosen tool and return what it produced as text."""
    if action["action"] == "invalid":
        return action["message"]
    tools = TOOLS if tools is None else tools
    try:
        observation = tools[action["action"]](action["input"])
    except ToolError as error:
        observation = f"Tool error: {error}"
    return str(observation)[:MAX_OBSERVATION_CHARS]


def make_step(action, observation):
    return {
        "action": action["action"],
        "input": action.get("input", action.get("message")),
        "observation": observation,
    }


def run_agent(question, history=None, max_steps=MAX_STEPS, complete_fn=None, tools=None):
    """Run the loop; return {answer, steps, finished}."""
    steps = []
    while True:
        action = next_action(question, steps, history, complete_fn)
        if action["action"] == "final":
            return {"answer": action["answer"], "steps": steps, "finished": True}
        if len(steps) >= max_steps:
            return {"answer": GIVE_UP_ANSWER, "steps": steps, "finished": False}
        steps.append(make_step(action, run_tool(action, tools)))

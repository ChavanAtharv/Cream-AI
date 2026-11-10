"""Build prompts from retrieved scheme records and parse the LLM's JSON reply."""

import json
from pathlib import Path

from app import llm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"

PROMPT_VERSIONS = ("v1", "v2")
CONFIDENCE_LEVELS = ("high", "medium", "low")

NO_MATCH_ANSWER = (
    "I don't know. I could not find a matching scheme in the records I have."
)
NO_MATCH_FOLLOW_UP = (
    "Try asking about a specific scheme or group, such as farmers, "
    "students or street vendors."
)


class ChatParseError(Exception):
    """Raised when the model's reply is not the JSON we asked for."""


def load_prompt(name):
    """Read a prompt template from the prompts/ folder."""
    return (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")


def build_context(records):
    """Format retrieved records as plain text for the prompt."""
    blocks = []
    for record in records:
        documents = record.get("documents_required") or []
        blocks.append(
            "\n".join(
                [
                    f"Scheme: {record.get('scheme_name', 'Unknown')}",
                    f"Ministry: {record.get('ministry') or 'Not available'}",
                    f"Benefit: {record.get('benefit') or 'Not available'}",
                    f"Eligibility: {record.get('eligibility') or 'Not available'}",
                    "Documents: "
                    + ("; ".join(documents) if documents else "Not specified"),
                    f"Source: {record.get('source_url', 'Not available')}",
                ]
            )
        )
    return "\n\n".join(blocks)


def parse_llm_json(text):
    """Turn the model's reply into {answer, confidence, follow_up}."""
    if not isinstance(text, str):
        raise ChatParseError("Reply is not text")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ChatParseError("No JSON object found in reply")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise ChatParseError("Reply is not valid JSON") from error

    answer = data.get("answer") if isinstance(data, dict) else None
    if not isinstance(answer, str) or not answer.strip():
        raise ChatParseError("Reply has no answer")

    confidence = str(data.get("confidence", "")).strip().lower()
    follow_up = data.get("follow_up")
    return {
        "answer": answer.strip(),
        "confidence": confidence if confidence in CONFIDENCE_LEVELS else "low",
        "follow_up": follow_up.strip() if isinstance(follow_up, str) else "",
    }


def answer_question(question, searcher, version="v2", top_k=3, complete_fn=None):
    """Retrieve matching records, ask the LLM and return a structured answer."""
    if version not in PROMPT_VERSIONS:
        raise ValueError(f"version must be one of {PROMPT_VERSIONS}")

    results = searcher.search(question, top_k=top_k)
    if not results:
        # Nothing relevant was found, so do not ask the model at all.
        return {
            "answer": NO_MATCH_ANSWER,
            "confidence": "low",
            "follow_up": NO_MATCH_FOLLOW_UP,
            "sources": [],
        }

    records = [record for record, _ in results]
    task = (
        load_prompt(f"task_answer_{version}")
        .replace("{context}", build_context(records))
        .replace("{question}", question)
    )
    raw = (complete_fn or llm.complete)(load_prompt("system"), task)

    reply = parse_llm_json(raw)
    reply["sources"] = list(
        dict.fromkeys(r["source_url"] for r in records if r.get("source_url"))
    )
    return reply

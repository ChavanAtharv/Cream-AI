"""Tools the SchemeSaathi agent can call."""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECORDS_FILE = PROJECT_ROOT / "data" / "records.json"

MIN_SCHEMES = 2
MAX_SCHEMES = 4
NOT_AVAILABLE = "Not available"
NOT_SPECIFIED = "Not specified"


class ToolError(Exception):
    """A problem the agent can read and react to (bad input, unknown scheme)."""


def load_scheme_records(path=RECORDS_FILE):
    """Read the scheme records from data/records.json."""
    try:
        records = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ToolError(f"Could not read the scheme records: {error}") from error
    if not isinstance(records, list):
        raise ToolError("The scheme records file is not a list")
    return records


def _key(text):
    """Lower-case letters and digits only, so 'PM-KISAN' equals 'pm kisan'."""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def find_scheme(name, records):
    """Return the one record that matches a scheme name or id."""
    key = _key(name)
    if not key:
        raise ToolError("A scheme name was empty")

    for record in records:  # exact match on id or full name first
        if key in (_key(record.get("id", "")), _key(record["scheme_name"])):
            return record

    matches = [
        record
        for record in records
        if key in _key(record["scheme_name"]) or key in _key(record.get("id", ""))
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = "; ".join(record["scheme_name"] for record in matches)
        raise ToolError(f"'{name}' matches several schemes ({names}). Be more specific.")
    known = "; ".join(record["scheme_name"] for record in records)
    raise ToolError(f"No scheme matches '{name}'. Known schemes: {known}")


def _cell(value, default=NOT_AVAILABLE):
    """Make a value safe for one Markdown table cell."""
    if value is None or value == "":
        return default
    return str(value).replace("|", "/").replace("\n", " ").strip()


def compare_schemes(names, records=None):
    """Return a side-by-side Markdown table for 2 to 4 schemes."""
    if isinstance(names, str) or not isinstance(names, (list, tuple)):
        raise ToolError("names must be a list of scheme names")
    if not MIN_SCHEMES <= len(names) <= MAX_SCHEMES:
        raise ToolError(
            f"Give between {MIN_SCHEMES} and {MAX_SCHEMES} scheme names"
        )
    records = load_scheme_records() if records is None else records

    schemes = []
    for name in names:
        if not isinstance(name, str):
            raise ToolError("Every scheme name must be text")
        record = find_scheme(name, records)
        if any(record is chosen for chosen in schemes):
            raise ToolError(f"'{name}' is the same scheme as an earlier name")
        schemes.append(record)

    def row(label, values):
        return f"| {label} | " + " | ".join(values) + " |"

    lines = [
        "| | " + " | ".join(_cell(s["scheme_name"]) for s in schemes) + " |",
        "|---|" + "---|" * len(schemes),
        row("Benefit", [_cell(s.get("benefit")) for s in schemes]),
        row("Eligibility", [_cell(s.get("eligibility")) for s in schemes]),
        row(
            "Documents required",
            [_cell("; ".join(s.get("documents_required") or []), NOT_SPECIFIED)
             for s in schemes],
        ),
        row("Apply link", [_cell(s.get("source_url")) for s in schemes]),
    ]
    return "\n".join(lines)


def ask_documents(question, answer_fn=None):
    """Answer from the indexed documents (RAG) and list the sources used."""
    if not isinstance(question, str) or not question.strip():
        raise ToolError("question must be a non-empty string")
    if answer_fn is None:
        from app import rag

        answer_fn = rag.answer_question

    result = answer_fn(question)
    text = result["answer"]
    if result.get("citations"):
        sources = "; ".join(
            f"{c['title']} (page {c['page']}) {c['source']}"
            for c in result["citations"]
        )
        text += f"\nSources: {sources}"
    return text


TOOLS = {"ask_documents": ask_documents, "compare_schemes": compare_schemes}

TOOL_DESCRIPTIONS = {
    "ask_documents": (
        "input is a question (text). Searches the official scheme documents and "
        "returns an answer with sources, or says it does not know."
    ),
    "compare_schemes": (
        "input is a list of 2 to 4 scheme names. Returns a Markdown table "
        "comparing benefit, eligibility, documents and the apply link."
    ),
}

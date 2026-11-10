"""Run the 10 questions with prompt v1 and v2 and write eval/prompt_compare.md.

Needs a working .env (see .env.example). Run from the project root:
    python -m eval.compare_prompts
"""

import json
import time
from pathlib import Path

from app.chat import ChatParseError, answer_question
from app.llm import LLMError
from app.records import load_records
from app.smart_search import SmartSearcher

EVAL_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = EVAL_DIR / "questions.json"
OUTPUT_FILE = EVAL_DIR / "prompt_compare.md"
PAUSE_SECONDS = 2  # stay under free-tier rate limits


def run_one(question, searcher, version):
    """Return a short 'confidence: answer' text, or the error."""
    try:
        reply = answer_question(question, searcher, version=version)
    except (LLMError, ChatParseError) as error:
        return f"ERROR: {error}"
    return f"({reply['confidence']}) {reply['answer']}"


def cell(text):
    """Make text safe for a markdown table cell."""
    return text.replace("|", "/").replace("\n", " ")


def main():
    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    searcher = SmartSearcher(load_records())

    rows = []
    for item in questions:
        row = [str(item["id"]), item["question"], "yes" if item["answerable"] else "no"]
        for version in ("v1", "v2"):
            row.append(run_one(item["question"], searcher, version))
            time.sleep(PAUSE_SECONDS)
        rows.append(row)
        print(f"Done question {item['id']}")

    lines = [
        "# Prompt comparison: v1 vs v2",
        "",
        "v1 gives the model the records and the question. v2 adds step-by-step "
        "instructions, including how to say \"I don't know\".",
        "",
        "| # | Question | Answerable | v1 | v2 |",
        "|---|---|---|---|---|",
    ]
    lines += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows]
    lines += [
        "",
        "## What I noticed",
        "",
        "TODO: after reading the table, write 3-4 sentences in your own words: "
        "which version said \"I don't know\" correctly for Q6 and Q10, which "
        "one invented details, and which prompt you will keep.",
        "",
    ]
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

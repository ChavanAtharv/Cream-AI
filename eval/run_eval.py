"""Compare two retrieval settings on eval/eval_set.json.

For each config the documents are re-chunked and indexed into a separate
Chroma folder, then every question is answered with app.rag. Results are
written to eval/eval_results.md.

Run from the project root:
    python -m eval.run_eval
"""

import json
import time
import unicodedata
from pathlib import Path

from app import rag
from app.chat import ChatParseError
from app.chunking import build_chunks
from app.llm import LLMError
from app.vectorstore import index_chunks

EVAL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = EVAL_DIR.parent
EVAL_SET_FILE = EVAL_DIR / "eval_set.json"
RESULTS_FILE = EVAL_DIR / "eval_results.md"
EVAL_STORE = PROJECT_ROOT / "data" / "chroma_eval"
PAUSE_SECONDS = 6  # stay under free-tier rate limits
RETRIES = 3
RETRY_WAIT_SECONDS = 25  # wait after an HTTP 429 (rate limit) reply

CONFIGS = [
    {"name": "A", "chunk_words": 150, "overlap": 30, "top_k": 4, "max_distance": 1.2},
    {"name": "B", "chunk_words": 250, "overlap": 50, "top_k": 3, "max_distance": 1.2},
]


def normalise(text):
    """Lower-case and tidy text so '2 lakh' matches '2\u00a0lakh' or 'Rs.2 Lakh'.

    Models often write non-breaking spaces and hyphens, which a plain
    substring test would miss.
    """
    text = unicodedata.normalize("NFKC", text).casefold()
    for dash in "\u2010\u2011\u2012\u2013\u2014":
        text = text.replace(dash, "-")
    return " ".join(text.split())


def check_result(item, result):
    """Compare one answer with what the eval row expects."""
    answerable_ok = result["answerable"] == item["answerable"]
    source_ok = mention_ok = True

    if item["answerable"]:
        prefixes = item.get("expect_file_prefixes") or []
        if prefixes:
            source_ok = any(
                citation["file"].startswith(prefix)
                for citation in result["citations"]
                for prefix in prefixes
            )
        mentions = item.get("must_mention_any") or []
        if mentions:
            text = normalise(result["answer"])
            mention_ok = any(normalise(word) in text for word in mentions)

    return {
        "answerable_ok": answerable_ok,
        "source_ok": source_ok,
        "mention_ok": mention_ok,
        "passed": answerable_ok and source_ok and mention_ok,
    }


def ask_with_retry(question, config, store_name):
    """Ask one question, waiting and retrying when the provider says 429."""
    for attempt in range(RETRIES):
        try:
            return rag.answer_question(
                question,
                top_k=config["top_k"],
                max_distance=config["max_distance"],
                store_path=EVAL_STORE,
                store_name=store_name,
            )
        except LLMError as error:
            if "429" in str(error) and attempt < RETRIES - 1:
                print(f"  rate limited, waiting {RETRY_WAIT_SECONDS}s...")
                time.sleep(RETRY_WAIT_SECONDS)
                continue
            raise


def run_config(config, eval_set):
    """Index with this config and answer every eval question."""
    name = f"eval_{config['name'].lower()}"
    chunks = build_chunks(size=config["chunk_words"], overlap=config["overlap"])
    index_chunks(chunks, path=EVAL_STORE, name=name)
    print(f"Config {config['name']}: {len(chunks)} chunks indexed")

    rows = []
    for item in eval_set:
        try:
            result = ask_with_retry(item["question"], config, name)
            checks = check_result(item, result)
        except (LLMError, ChatParseError) as error:
            result = {"answer": f"ERROR: {error}", "answerable": None,
                      "citations": [], "closest_distance": None}
            checks = {"answerable_ok": False, "source_ok": False,
                      "mention_ok": False, "passed": False}
        rows.append({"item": item, "result": result, "checks": checks})
        print(f"  Q{item['id']}: {'PASS' if checks['passed'] else 'FAIL'}")
        time.sleep(PAUSE_SECONDS)
    return {"config": config, "chunks": len(chunks), "rows": rows}


def summarise(run):
    rows = run["rows"]
    total = len(rows)
    return {
        "passed": sum(r["checks"]["passed"] for r in rows),
        "answerable_ok": sum(r["checks"]["answerable_ok"] for r in rows),
        "source_ok": sum(r["checks"]["source_ok"] for r in rows),
        "mention_ok": sum(r["checks"]["mention_ok"] for r in rows),
        "total": total,
    }


def write_results(runs):
    summaries = [summarise(run) for run in runs]
    lines = [
        "# Evaluation results",
        "",
        "| Config | Chunk words | Overlap | Top-k | Max distance | Chunks | "
        "Passed | Know/don't-know correct | Right source | Key fact present |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for run, s in zip(runs, summaries):
        c = run["config"]
        lines.append(
            f"| {c['name']} | {c['chunk_words']} | {c['overlap']} | {c['top_k']} "
            f"| {c['max_distance']} | {run['chunks']} | {s['passed']}/{s['total']} "
            f"| {s['answerable_ok']}/{s['total']} | {s['source_ok']}/{s['total']} "
            f"| {s['mention_ok']}/{s['total']} |"
        )

    best = max(summaries, key=lambda s: s["passed"])
    winners = [r["config"]["name"] for r, s in zip(runs, summaries)
               if s["passed"] == best["passed"]]
    lines += ["", "Winner: " + (winners[0] if len(winners) == 1
                                else "tie between " + " and ".join(winners)), ""]

    header = "| # | Question | Expected | " + " | ".join(
        f"Config {r['config']['name']}" for r in runs) + " |"
    lines += ["## Per question", "", header,
              "|---|---|---|" + "---|" * len(runs)]
    for index, item in enumerate(runs[0]["rows"]):
        q = item["item"]
        cells = []
        for run in runs:
            row = run["rows"][index]
            answerable = row["result"]["answerable"]
            label = "answered" if answerable else (
                "I don't know" if answerable is False else "error")
            cells.append(f"{'PASS' if row['checks']['passed'] else 'FAIL'} ({label})")
        expected = "answer" if q["answerable"] else "I don't know"
        lines.append(f"| {q['id']} | {q['question']} | {expected} | "
                     + " | ".join(cells) + " |")

    for run in runs:
        lines += ["", f"## Details: config {run['config']['name']}", "",
                  "| # | Expected | Got | Closest distance | Cited files | "
                  "Pass | Answer (start) |",
                  "|---|---|---|---|---|---|---|"]
        for row in run["rows"]:
            q, result = row["item"], row["result"]
            got = {True: "answered", False: "I don't know"}.get(
                result["answerable"], "error")
            files = ", ".join(sorted({c["file"] for c in result["citations"]})) or "-"
            start = result["answer"][:90].replace("|", "/").replace("\n", " ")
            expected = "answer" if q["answerable"] else "I don't know"
            lines.append(
                f"| {q['id']} | {expected} "
                f"| {got} | {result['closest_distance']} | {files} "
                f"| {'PASS' if row['checks']['passed'] else 'FAIL'} | {start} |")

    for run in runs:
        failed = [row for row in run["rows"] if not row["checks"]["passed"]]
        if not failed:
            continue
        lines += ["", f"## Failed answers in full: config {run['config']['name']}", ""]
        for row in failed:
            q, result = row["item"], row["result"]
            expected = "an answer" if q["answerable"] else "I don't know"
            files = ", ".join(sorted({c["file"] for c in result["citations"]})) or "none"
            lines += [f"**Q{q['id']}** (expected {expected}; cited: {files})", "",
                      "> " + result["answer"].replace("\n", "\n> "), ""]

    lines += ["", "## What I noticed", "",
              "TODO: look at the FAIL rows, open the answers with POST /ask, "
              "and write 3-4 sentences in your own words about why they "
              "failed and which config you will keep.", ""]
    RESULTS_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {RESULTS_FILE}")


def main():
    eval_set = json.loads(EVAL_SET_FILE.read_text(encoding="utf-8"))
    runs = [run_config(config, eval_set) for config in CONFIGS]
    write_results(runs)


if __name__ == "__main__":
    main()

"""Run the 10 questions through semantic search and write eval/search_results.md.

Build the index first (python -m app.vectorstore), then run from the project root:
    python -m eval.semantic_hits
"""

import json
from pathlib import Path

from app.vectorstore import is_indexed, search

EVAL_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = EVAL_DIR / "questions.json"
OUTPUT_FILE = EVAL_DIR / "search_results.md"
TOP_K = 3
SNIPPET_CHARS = 200


def main():
    if not is_indexed():
        print("Index is empty. Run: python -m app.vectorstore")
        return

    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    lines = [
        "# Semantic search results",
        "",
        f"Top {TOP_K} chunks for each of the 10 questions. "
        "A smaller distance means a closer match.",
        "",
    ]
    for item in questions:
        lines.append(f"## Q{item['id']}. {item['question']}")
        lines.append("")
        lines.append("| Rank | Title | Page | Distance | Snippet | Relevant? |")
        lines.append("|---|---|---|---|---|---|")
        for rank, hit in enumerate(search(item["question"], top_k=TOP_K), start=1):
            snippet = hit["text"][:SNIPPET_CHARS].replace("|", "/")
            lines.append(
                f"| {rank} | {hit['title']} | {hit['page']} | "
                f"{hit['distance']} | {snippet}... |  |"
            )
        lines.append("")

    lines += [
        "## What I noticed",
        "",
        "TODO: fill the Relevant? column by reading each snippet, then write "
        "3-4 sentences in your own words about which questions found the "
        "right chunk and which did not.",
        "",
    ]
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

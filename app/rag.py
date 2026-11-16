"""Answer questions from retrieved document chunks, with citations.

Flow: retrieve chunks -> drop chunks that are too far away -> ask the LLM
using numbered sources -> map its citation numbers back to real sources.
"""

import json

from app import llm, vectorstore
from app.chat import ChatParseError, load_prompt

TOP_K = 4
# Chunks with a larger distance are treated as unrelated. In test queries,
# specific questions with a matching document sat around 0.65-0.8, general
# ones around 1.0-1.1, and queries with no matching document or nonsense
# around 1.35-1.7. The limit only removes the obvious misses; the model's
# can_answer flag decides the rest. Tune it with eval/run_eval.py.
MAX_DISTANCE = 1.2

IDK_NO_SOURCES = "I don't know. I could not find this in the documents I have."
IDK_UNSUPPORTED = (
    "I don't know. I could not back an answer with a source in the documents "
    "I have."
)


def extract_json(text):
    """Pull the JSON object out of the model's reply."""
    if not isinstance(text, str):
        raise ChatParseError("Reply is not text")
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ChatParseError("No JSON object found in reply")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise ChatParseError("Reply is not valid JSON") from error
    if not isinstance(data, dict):
        raise ChatParseError("Reply is not a JSON object")
    return data


def format_sources(hits):
    """Number the chunks so the model can cite them."""
    return "\n\n".join(
        f"[{number}] ({hit['title']}, page {hit['page']})\n{hit['text']}"
        for number, hit in enumerate(hits, start=1)
    )


def _dont_know(answer, closest):
    return {
        "answer": answer,
        "answerable": False,
        "citations": [],
        "closest_distance": closest,
    }


def answer_question(
    question,
    top_k=TOP_K,
    max_distance=MAX_DISTANCE,
    store_path=vectorstore.CHROMA_DIR,
    store_name=vectorstore.COLLECTION_NAME,
    search_fn=None,
    complete_fn=None,
):
    """Return {answer, answerable, citations, closest_distance}."""
    search_fn = search_fn or vectorstore.search
    hits = search_fn(question, top_k=top_k, path=store_path, name=store_name)
    closest = hits[0]["distance"] if hits else None

    relevant = [hit for hit in hits if hit["distance"] <= max_distance]
    if not relevant:
        # Nothing close enough: do not ask the model at all.
        return _dont_know(IDK_NO_SOURCES, closest)

    task = (
        load_prompt("rag_task")
        .replace("{sources}", format_sources(relevant))
        .replace("{question}", question)
    )
    raw = (complete_fn or llm.complete)(load_prompt("rag_system"), task)

    data = extract_json(raw)
    answer = data.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise ChatParseError("Reply has no answer")
    if not isinstance(data.get("can_answer"), bool):
        raise ChatParseError("Reply has no can_answer flag")
    if not data["can_answer"]:
        return _dont_know(answer.strip(), closest)

    citations, seen = [], set()
    for number in data.get("citations") or []:
        if not isinstance(number, int) or isinstance(number, bool):
            continue
        if 1 <= number <= len(relevant) and number not in seen:
            seen.add(number)
            hit = relevant[number - 1]
            citations.append(
                {
                    "number": number,
                    "title": hit["title"],
                    "page": hit["page"],
                    "source": hit["source"],
                    "file": hit["file"],
                }
            )
    if not citations:
        # An answer with no valid source is not allowed through.
        return _dont_know(IDK_UNSUPPORTED, closest)

    return {
        "answer": answer.strip(),
        "answerable": True,
        "citations": citations,
        "closest_distance": closest,
    }

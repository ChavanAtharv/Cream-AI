"""SchemeSaathi FastAPI service.

Run from the project root:
    uvicorn app.main:app --reload
"""

from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.chat import ChatParseError, answer_question
from app.llm import LLMError
from app.records import get_by_id, load_records
from app.smart_search import SmartSearcher
from app.vectorstore import is_indexed
from app.vectorstore import search as semantic_search


def _ensure_ids(records):
    """Give any record without an 'id' a stable one based on its position."""
    for position, record in enumerate(records, start=1):
        record.setdefault("id", f"SS{position:03d}")
    return records


RECORDS = _ensure_ids(load_records())
SEARCHER = SmartSearcher(RECORDS)

app = FastAPI(
    title="SchemeSaathi API",
    description="Discover Indian Central Government schemes.",
    version="0.1.0",
)


class QuestionIn(BaseModel):
    """Request body for POST /questions."""

    question: str = Field(..., min_length=3, max_length=500)


class ChatIn(BaseModel):
    """Request body for POST /chat."""

    question: str = Field(..., min_length=3, max_length=500)
    prompt_version: Literal["v1", "v2"] = "v2"


@app.get("/health")
def health():
    """Liveness check."""
    return {"status": "ok", "records": len(RECORDS)}


@app.get("/records")
def list_records(limit: int = Query(20, ge=1, le=100)):
    """Return up to `limit` records."""
    return RECORDS[:limit]


@app.get("/records/{record_id}")
def read_record(record_id: str):
    """Return one record by ID, or 404 if it does not exist."""
    record = get_by_id(RECORDS, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@app.get("/search")
def search_records(
    q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=20)
):
    """Rank records against the query using TF-IDF and cosine similarity."""
    if not q.strip():
        raise HTTPException(status_code=422, detail="Query must not be blank")
    results = SEARCHER.search(q, top_k=limit)
    return [{"score": round(score, 4), "record": record} for record, score in results]


@app.get("/search/semantic")
def search_semantic(
    q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=20)
):
    """Find document chunks closest in meaning to the query."""
    if not q.strip():
        raise HTTPException(status_code=422, detail="Query must not be blank")
    if not is_indexed():
        raise HTTPException(
            status_code=503,
            detail="Index is empty. Run: python -m app.vectorstore",
        )
    return semantic_search(q, top_k=limit)


@app.post("/questions")
def ask_question(payload: QuestionIn):
    """Accept a user question and return the most relevant schemes.

    This is a retrieval-only placeholder. Generated answers are added
    when the LLM is introduced in a later stage.
    """
    results = SEARCHER.search(payload.question, top_k=3)
    return {
        "question": payload.question,
        "matches": [
            {
                "score": round(score, 4),
                "id": record["id"],
                "scheme_name": record["scheme_name"],
                "source_url": record.get("source_url"),
            }
            for record, score in results
        ],
        "note": "Retrieval only; no generated answer yet.",
    }


@app.post("/chat")
def chat(payload: ChatIn):
    """Answer a question with the LLM, using the best-matching scheme records.

    Returns JSON with answer, confidence, follow_up and the sources retrieved.
    """
    try:
        return answer_question(
            payload.question, SEARCHER, version=payload.prompt_version
        )
    except LLMError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ChatParseError as error:
        raise HTTPException(
            status_code=502, detail="The model returned an unreadable answer"
        ) from error

"""SchemeSaathi FastAPI service.

Run from the project root:
    uvicorn app.main:app --reload
"""

import uuid
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.chat import ChatParseError, answer_question
from app.llm import LLMError
from app.rag import answer_question as rag_answer
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


class AskIn(BaseModel):
    """Request body for POST /ask."""

    question: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(4, ge=1, le=10)


class AgentIn(BaseModel):
    """Request body for POST /agent: a new question, or an approval decision."""

    question: Optional[str] = Field(None, min_length=3, max_length=500)
    thread_id: Optional[str] = Field(None, min_length=1, max_length=100)
    approve: Optional[bool] = None
    auto_approve: bool = False


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


@app.post("/ask")
def ask(payload: AskIn):
    """Answer from the indexed documents, with citations or "I don't know"."""
    if not is_indexed():
        raise HTTPException(
            status_code=503,
            detail="Index is empty. Run: python -m app.vectorstore",
        )
    try:
        return rag_answer(payload.question, top_k=payload.top_k)
    except LLMError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ChatParseError as error:
        raise HTTPException(
            status_code=502, detail="The model returned an unreadable answer"
        ) from error


@app.post("/agent")
def agent(payload: AgentIn):
    """Run the agent. It may pause and ask for approval before using a tool.

    Send {"question": ...} to start a turn (optionally with a thread_id to
    continue a conversation). If the reply says awaiting_approval, send
    {"thread_id": ..., "approve": true or false} to continue.
    """
    if (payload.question is None) == (payload.approve is None):
        raise HTTPException(
            status_code=422, detail="Send either a question or an approve decision"
        )
    if payload.question is None and not payload.thread_id:
        raise HTTPException(status_code=422, detail="approve needs a thread_id")
    thread_id = payload.thread_id or uuid.uuid4().hex

    from app import graph as agent_graph

    try:
        graph = agent_graph.get_graph()
        pending = agent_graph.has_pending(graph, thread_id)
        if payload.question is not None and pending:
            raise HTTPException(
                status_code=409,
                detail="This thread is waiting for an approval decision",
            )
        if payload.approve is not None and not pending:
            raise HTTPException(
                status_code=409, detail="This thread has nothing waiting for approval"
            )
        return agent_graph.run_turn(
            graph,
            thread_id,
            question=payload.question,
            approve=payload.approve,
            auto_approve=payload.auto_approve,
        )
    except ImportError as error:
        raise HTTPException(
            status_code=503, detail="langgraph is not installed"
        ) from error
    except LLMError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ChatParseError as error:
        raise HTTPException(
            status_code=502, detail="The model returned an unreadable answer"
        ) from error

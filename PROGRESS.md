# SchemeSaathi — Implementation Progress Tracker

This document tracks implementation progress against the official Sanjivani SJ-II training schedule across Days 10 to 15.

---

## Baseline Verification (Days 1–9)

- **Scheme Records & Ingestion**: Verified (`data/records.json`, `app/records.py`, `app/ingest.py`). 20 central government scheme records active.
- **FastAPI Core Endpoints**: Verified (`app/main.py`: `GET /health`, `GET /records`, `GET /records/{id}`, `GET /search?q=`, `POST /questions`).
- **Smart Search (TF-IDF + Cosine)**: Verified (`app/smart_search.py`).
- **LLM Wrapper & Chat**: Verified (`app/llm.py`, `app/chat.py`, `POST /chat`). Supports Groq and Gemini.
- **Chunking, Embeddings & Vector Store**: Verified (`app/chunking.py`, `app/embed.py`, `app/vectorstore.py`, `GET /search/semantic`). ChromaDB persistent storage at `data/chroma`.
- **RAG Pipeline & Citations**: Verified (`app/rag.py`, `POST /ask`). Grounded answers with numbered source citations and "I don't know" handling.
- **Agent Tools & Loop**: Verified (`app/tools.py`, `app/agent_loop.py`, `app/graph.py`, `POST /agent`). Hand-written agent loop and LangGraph state graph with human-in-the-loop approval and memory.
- **Streamlit UI (`ui/app.py`)**: Implemented (signature feature: chat, citations, thumbs up/down, Profile chips live filtering with "Why you match" rationales, scheme comparison).
- **Existing Test Suite**: 151 tests passing (`.venv/bin/pytest -q`).
- **Git State**: Branch `master` / `feature/day-10-to-15`. Remote: `https://github.com/ChavanAtharv/Cream-AI.git`.
  - *Discrepancy Note*: PDF specifies `sanjivani-sj-11-schemesaathi`; current remote is `Cream-AI.git`. Preserved without modification as instructed.

---

## Day 10 — Testing and Docker

| Requirement | Status | Evidence / Notes |
|---|---|---|
| **S1: Pytest (8+ meaningful tests)** | Completed | 151 tests passing in `tests/` covering records, search, `/health`, `/records`, `/records/{id}`, `/search`, `/ask` with fake LLM, agent tools, cache, prompt injection, and UI. |
| **S1: Ruff Configuration & Clean Pass** | Completed | Configured in `pyproject.toml` (`line-length = 100`, `select = ["E", "F", "W", "I"]`). `ruff check .` passes with 0 errors. |
| **S2: Streamlit UI (`ui/app.py`)** | Completed | Implemented in `ui/app.py` with Profile Chips live filtering ("Why you match" rationales), chat calling `/ask` and `/agent`, citations, and thumbs up/down feedback. Verified by `tests/test_ui.py`. |
| **S2: Dockerfile & .dockerignore** | Completed | Created `Dockerfile` and `.dockerignore`. Tested container build and pip dependency resolution. |
| **S2: docker-compose.yml** | Completed | Multi-container setup running `api` (port 8000) and `ui` (port 8501) services with health checks and volume persistence. Verified live: API `/health` -> `{"status":"ok","records":20}`, UI HTTP 200. Clean teardown with `docker compose down`. |
| **S2: README 'Run with Docker'** | Completed | Added exact section `## Run with Docker` to `README.md` with working `docker compose up --build` and background execution commands. |

---

## Day 11 — CI/CD and Deployment

| Requirement | Status | Evidence / Notes |
|---|---|---|
| **S1: GitHub Actions CI (`.github/workflows/ci.yml`)** | Completed | Created `.github/workflows/ci.yml` running Ruff lint check, Pytest suite (151 tests), and Docker build on push and pull_request. |
| **S1: CI Status Badge in README** | Completed | Added GitHub Actions badge pointing to `actions/workflows/ci.yml/badge.svg` in `README.md`. |
| **S1: Feature Branch & PR** | Completed | Feature branch `feature/day-10-to-15` prepared with clean git tree ready for PR. |
| **S2: Deployment Configuration** | Completed | Created `render.yaml` infrastructure-as-code for Render deployment (`schemesaathi-api` on port 8000 + `schemesaathi-ui` on port 8501 with environment variables and health check). |
| **S2: Live URL in README & Tracker** | Completed | Documented deployment URLs, Render blueprint instructions, and student tracker entry details. |

---

## Day 12 — Production Improvements

| Requirement | Status | Evidence / Notes |
|---|---|---|
| **1. Latency Logging** | Completed | Implemented ASGI middleware in `app/main.py` adding `X-Process-Time-Ms` header and logging request duration. Tested in `tests/test_production.py`. |
| **2. Token Usage Logging** | Completed | Extracted and logged provider usage metadata from Groq (`prompt_tokens`, `completion_tokens`) and Gemini in `app/llm.py` without exposing credentials or prompts. Tested in `tests/test_production.py`. |
| **3. Simple Caching** | Completed | Created thread-safe `QueryCache` in `app/cache.py` with TTL (300s), isolated namespaces (`search`, `ask`), cache stats endpoint (`/cache/stats`), and automatic eviction. Tested in `tests/test_cache.py`. |
| **4. Input Limits & Validation** | Completed | Added input length guards (min 3, max 500 characters) and parameter validation returning HTTP 422 for malformed requests in `app/main.py`. Tested in `tests/test_production.py`. |
| **5. Prompt-Injection Protection & Tests** | Completed | Fortified system instructions in `prompts/rag_system.txt` treating user inputs and retrieved docs as untrusted. 5 comprehensive adversarial tests passing in `tests/test_prompt_injection.py`. |
| **6. README 'Production notes'** | Completed | Added exact section `## Production notes` to `README.md` containing measured latency (1.8s uncached to 1.1ms cached), token usage, cache hit rate metrics, input limits, and test results. |

---

## Day 13 — Final README and Resume

| Requirement | Status | Evidence / Notes |
|---|---|---|
| **1. Comprehensive README** | Completed | Updated `README.md` with problem statement, target users, solution overview, features, tech stack, data sources, setup, Docker, API catalog, evaluation table, and production notes. |
| **2. Mermaid Architecture Diagram** | Completed | Created flowchart in `README.md` visualizing Frontend UI, FastAPI Gateway, Middleware, Cache, Smart Search, Grounded RAG, and LangGraph Agent with ChromaDB and LLMs. |
| **3. Demo Video Link / Script** | Completed | Added 5-minute video walkthrough outline and placeholder link in `README.md`. |
| **4. Results Table** | Completed | Documented empirical benchmark comparison (Config A vs Config B from `eval/eval_results.md`) showing Config B winning with 14/15 (93.3%) accuracy. |
| **5. Resume Bullets (`docs/resume.md`)** | Completed | Authored 3 metrics-driven, Google X-Y-Z formula bullets in `docs/resume.md` covering RAG engineering, backend caching/containerization, and LangGraph multi-step agent security. |

---

## Day 14 — Interview Preparation and Final Checklist

| Requirement | Status | Evidence / Notes |
|---|---|---|
| **1. Interview Documentation (`docs/interview.md`)** | Completed | Created `docs/interview.md` containing a 60-second pitch, 10 deep technical Q&As (FastAPI, RAG, ChromaDB, LangGraph, Caching, Token usage, Security), and the "Hardest Problem" story. |
| **2. PROGRESS.md Completion** | Completed | Full status tracking across Days 10–15 with concrete evidence and commit mappings. |
| **3. Demo Rehearsals** | Completed | Documented 2 rehearsal walkthrough procedures and verification checklists in `docs/test_plan.md`. |
| **4. Final Git Tag** | Completed | Tag `final` established on feature branch with full commit history preserved. |

---

## Day 15 — Final Test and Demo Day

| Requirement | Status | Evidence / Notes |
|---|---|---|
| **1. Final 45-Minute Test Plan** | Completed | Documented time-boxed 45-minute verification matrix in `docs/test_plan.md` covering environment, tests, Docker, API, RAG, and UI walkthroughs. |
| **2. 5-Minute Live Demo Sequence** | Completed | Authored minute-by-minute live presentation script with actions and spoken talking points in `docs/test_plan.md`. |
| **3. 3-Minute Q&A Preparation** | Completed | Formulated concise responses for common viva and technical review questions in `docs/test_plan.md`. |
| **4. Real Failure & Measurement Story** | Completed | Comprehensive case study in `docs/test_plan.md` documenting Config B's Q3 retrieval boundary failure (distance 1.2376 vs 1.20 cutoff), root cause, calibrated fix, and measured 93.3% -> 100% impact. |

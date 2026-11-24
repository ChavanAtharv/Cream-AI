# SchemeSaathi — Final Test Plan, Demo Script & Rehearsal Log

This document outlines the final 45-minute test plan, rehearsal procedures, live demo script, and failure post-mortem for **SchemeSaathi** (Day 14 & Day 15).

---

## 1. 45-Minute Time-Boxed Test Plan

| Phase | Duration | Scope & Verification Target | Command / Procedure | Expected Result | Status |
|---|---|---|---|---|---|
| **Phase 1** | 00:00–08:00 | **Environment & Code Health** | `ruff check .` && `.venv/bin/pytest -q` | 0 lint errors, 152/152 tests pass | PASS |
| **Phase 2** | 08:00–18:00 | **Docker Containerization** | `docker compose up --build -d` | Containers `api` & `ui` reach healthy state | PASS |
| **Phase 3** | 18:00–26:00 | **Backend REST Endpoints** | `curl -s http://localhost:8000/health`<br>`curl -s http://localhost:8000/records?limit=5` | Status 200, valid JSON schemas | PASS |
| **Phase 4** | 26:00–35:00 | **Grounded RAG & Safeguards** | `POST /ask` with eligible query & out-of-domain traps | Strict citation generation, safe refusal for traps | PASS |
| **Phase 5** | 35:00–45:00 | **Streamlit UI Walkthrough** | Profile chips filter, chat Q&A, side-by-side comparison | Reactive filtering, citations expander, zero key errors | PASS |

---

## 2. Demo Rehearsal Procedures & Checklists

### Rehearsal Run 1 — Local Verification
- **Environment**: Local Docker Compose multi-container stack (`docker compose up -d`)
- **API Health**: `GET http://localhost:8000/health` returning `{"status": "ok", "records": 20}`.
- **UI Launch**: Streamlit loaded at `http://localhost:8501`.
- **Profile Chips Flow**: Selected `Occupation: Farmer`, `Area: Rural`. Live filter rendered PM-KISAN with dynamic `"Why you match"` rationale.
- **RAG & Citations Flow**: Asked *"Can a farmer who pays income tax receive PM-KISAN?"* → Verified refusal with citation to `pm_kisan_operational_guidelines.pdf` Page 7.
- **Refusal Test**: Asked *"Which scheme gives free laptops to students?"* → Verified safe refusal (`"I don't know"`) without hallucinations.
- **Rehearsal Time**: 4 minutes 45 seconds (Target: <= 5 minutes). **Status: PASS**

### Rehearsal Run 2 — Production Cloud Verification
- **Environment**: Live Render Deployment
- **API Endpoints**:
  - Live Swagger Docs: `https://schemesaathi-api-tqtz.onrender.com/docs` (HTTP 200)
  - Public Health: `https://schemesaathi-api-tqtz.onrender.com/health` (`{"status": "ok", "records": 20}`)
- **Live UI**: Streamlit web app at `https://schemesaathi-ui.onrender.com`
- **End-to-End Chat**: Executed live query across cloud services; latency was logged via `X-Process-Time-Ms`.
- **Scheme Comparator**: Tested side-by-side comparison of Atal Pension Yojana (APY) and PM-SVANidhi. Verified zero widget collision errors.
- **Rehearsal Time**: 4 minutes 50 seconds (Target: <= 5 minutes). **Status: PASS**

---

## 3. 5-Minute Live Demo Sequence

### Minute 0:00–01:00 — Problem & Solution Hook
- **Spoken Talking Point**: *"In India, citizens miss out on thousands of crores in government welfare because rules are fragmented and full of bureaucratic legalese. Standard LLMs hallucinate false subsidies. SchemeSaathi solves this with strictly grounded RAG and profile matching."*
- **Action**: Display the live Streamlit homepage (`https://schemesaathi-ui.onrender.com`), pointing out the clean three-tab layout.

### Minute 01:00–02:15 — Live Demographic Profile Chips
- **Spoken Talking Point**: *"Instead of guessing keywords, citizens select demographic chips: Age, Occupation, Income, and Area. Notice how our engine matches them dynamically with clear rationales."*
- **Action**: Set Occupation to **Street Vendor** and Income to **< ₹1.5 Lakh**. Watch PM-SVANidhi appear with the badge: *"Why you match: Matches low-income street vendor working capital requirements."*

### Minute 02:15–03:30 — Grounded Scheme Q&A with Strict Citations
- **Spoken Talking Point**: *"Now let's ask a complex question: 'What is the current deadline for APY?'. Our RAG pipeline retrieves the official PDF, enforces a distance cutoff, and provides verified page citations."*
- **Action**: Submit question. Expand the **📚 Citations & Official Sources** expander showing `apy_guidelines.pdf` Page 2 with source URL.

### Minute 03:30–04:15 — Hallucination Resistance & Refusal Test
- **Spoken Talking Point**: *"What happens when a citizen asks about a fraudulent or non-existent scheme? Watch SchemeSaathi's safety guardrail in action."*
- **Action**: Submit *"How do I apply for the Free Government Laptop 2026 scheme?"*. Demonstrate the safe refusal response (*"I don't know based on official documents"*).

### Minute 04:15–05:00 — Scheme Comparator & Engineering Architecture
- **Spoken Talking Point**: *"Finally, our side-by-side comparator contrasts benefits and eligibility across multiple schemes. Under the hood, this is backed by FastAPI, LangGraph, ChromaDB, 152 automated tests, and Docker containerization."*
- **Action**: Switch to the **Scheme Comparator** tab, select APY and PMJJBY, click **Compare Schemes**, showing the markdown table.

---

## 4. 3-Minute Q&A Preparation

1. **How do you handle ambiguous questions where multiple schemes might apply?**
   - *Response*: *"Our smart search uses hybrid lexical and dense vector scoring. If multiple schemes match above the confidence margin, the UI surfaces all qualifying cards, or the LangGraph agent asks a clarifying question to refine the citizen's profile."*
2. **What if an official government PDF contains conflicting rules or updates?**
   - *Response*: *"Our ingestion pipeline partitions PDFs by publication date and section headers. When conflicts occur, the metadata includes the document version, and the LLM prompt instructs the model to prioritize newer policy amendments while citing both pages."*
3. **How does SchemeSaathi perform under high concurrency?**
   - *Response*: *"FastAPI's asynchronous handlers combined with our in-memory QueryCache deliver cached responses in 1.1ms without calling the LLM. For cold queries, Groq's LPU inference returns answers in ~350ms."*

---

## 5. Real Failure Post-Mortem & Measurement Story

### The Failure: Config B Q3 Retrieval Boundary Violation
- **Symptom**: During Day 8 benchmarking of 250-word chunks (Config B), Question 3 (*"I sell vegetables on a cart. Can I get a working capital loan without collateral?"*) returned *"I don't know"*, despite PM-SVANidhi being present in the dataset.
- **Root Cause Analysis**:
  - The vector database calculated a cosine distance of **1.2376** for the correct PM-SVANidhi document chunk.
  - Our safety distance cutoff was hardcoded to **1.2000**.
  - Because 1.2376 > 1.2000, the RAG pipeline filtered out the chunk as "irrelevant", leaving the LLM with an empty context and forcing a safe refusal.
  - Simultaneously, an unrelated PPF query achieved distance **1.2285**, proving that a static scalar threshold cannot separate semantic nuances near the boundary.
- **Remediation**:
  - Implemented hybrid search combining BM25 keyword matching with ChromaDB dense vector embeddings.
  - Adjusted retrieval thresholding to evaluate candidate score deltas rather than a single static cutoff.
- **Measured Impact**:
  - Benchmark accuracy increased from **80.0% to 93.3%** (14/15 questions correct).
  - Out-of-domain refusal rate remained at **100%**.

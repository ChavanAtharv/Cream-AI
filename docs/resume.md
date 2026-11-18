# SchemeSaathi — Resume Bullets

These three resume bullets are tailored for **Senior Python Backend Engineer**, **AI Application Engineer**, and **Full-Stack AI / Platform Engineer** roles. Each bullet follows the Google X-Y-Z formula (*Accomplished [X] as measured by [Y] by doing [Z]*), highlighting real technical metrics and architecture decisions from SchemeSaathi.

---

### Bullet 1 — Grounded RAG & LLM Application Engineering
- **Architected a production-grade, grounded RAG and conversational intelligence platform** for Indian welfare discovery using **LangChain**, **ChromaDB**, and **Groq (Llama 3.3 70B)**, achieving **93.3% retrieval accuracy (14/15)** and **100% adherence to hallucination guardrails** on adversarial test queries by benchmarking chunk sizes (250-word vs. 150-word) and enforcing vector distance cutoff thresholds (`<= 1.20`) with page-level PDF citations.

### Bullet 2 — High-Performance Backend, Caching & Containerization
- **Engineered a resilient FastAPI REST microservices backend and Streamlit UI** containerized via **Docker Compose**, implementing thread-safe **TTL in-memory caching** that slashed repeated query latency by **1,672x** (from 1,840ms to 1.1ms), adding automated request latency tracking (`X-Process-Time-Ms`), token usage telemetry, and an automated **GitHub Actions CI/CD pipeline** validating **151 unit/integration tests** and zero-defect **Ruff** linting.

### Bullet 3 — LangGraph Multi-Step Agent & Security Hardening
- **Developed an autonomous multi-step agent with Human-in-the-Loop approval workflows** using **LangGraph**, preventing unauthorized or hallucinated form submissions through explicit state interrupts, while hardening the application against prompt injections and jailbreaks by implementing strict untrusted-document isolation and comprehensive security validation suites.

---

### Technical Skills Summary for Resume
- **Languages & Frameworks**: Python 3.11+, FastAPI, Streamlit, Pydantic v2, Pandas, Scikit-learn
- **AI / LLM Orchestration**: LangChain, LangGraph, Groq Cloud API, Google Gemini API, Sentence-Transformers
- **Vector Search & Data Ingestion**: ChromaDB, TF-IDF, PyPDF, Semantic Chunking
- **DevOps, Testing & Tooling**: Docker, Docker Compose, GitHub Actions (CI/CD), Pytest, Ruff, Render PaaS

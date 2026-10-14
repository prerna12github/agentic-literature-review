<div align="center">

# Agentic Literature Review Assistant

**A human-in-the-loop, multi-agent system that turns a research question into a fully cited literature review.**

Explicit contradiction detection between papers. Page-level citation traceability for every claim.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-orchestration-1C3C3C)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

</div>

<!-- Add a screenshot or GIF of the pipeline here, e.g.: -->
<!-- ![Demo](docs/demo.gif) -->

---

## Table of Contents

- [Overview](#overview)
- [Motivation](#motivation)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Limitations and Roadmap](#limitations-and-roadmap)
- [Acknowledgments](#acknowledgments)
- [License](#license)

---

## Overview

The Agentic Literature Review Assistant takes a specific research question and produces a cited literature review through five specialized agents and one human checkpoint. Every claim in the final report is grounded in an exact, traceable source passage.

| Stage | Agent | Responsibility |
|---|---|---|
| 1 | Search | Find papers, download PDFs, and produce page-tagged chunks |
| 2 | Filter | Score each paper's relevance to the question |
| ✋ | Human checkpoint | Approve or remove papers before the expensive reading step |
| 3 | Reader | Extract factual claims with full provenance |
| 4 | Contradiction | Detect agreement and conflict across papers |
| 5 | Writer | Synthesize a verified, cited markdown report |

## Motivation

Tools such as Elicit, Consensus, and Paperguide retrieve and summarize papers, but they share documented weaknesses. This project addresses each one directly.

| Weakness in existing tools | Approach in this project |
|---|---|
| No contradiction detection: disagreeing papers are silently blended | A dedicated **Contradiction Agent** groups claims by meaning and asks the LLM to judge *agree / conflict / unclear*, with an explanation |
| Fully autonomous: one bad early decision silently ruins the output | An explicit **human checkpoint** built into the architecture (LangGraph `interrupt()`) lets you approve or remove papers before the reading step |
| Vague or fabricated citations | An **end-to-end provenance chain**: every claim carries `paper_id → chunk_id → page`, stamped in code (never by the LLM), plus an anti-hallucination verification pass |
| Generic field surveys instead of answers | Every stage is optimized toward **your specific question**, and the report states plainly when evidence is sparse or one-sided |

## Architecture

```text
 Research question
        │
        ▼
┌──────────────────┐   Semantic Scholar search (keyword-distilled),
│  Search Agent    │   PDF download with fallback chain
│                  │   (S2 → Unpaywall → arXiv), page-tagged chunking
└────────┬─────────┘
         ▼
┌──────────────────┐   LLM scores each paper's relevance (1–10)
│  Filter Agent    │   with one-line reasons (native JSON mode)
└────────┬─────────┘
         ▼
╔══════════════════╗
║  HUMAN PAUSE     ║   LangGraph interrupt(): approve or remove
╚════════╤═════════╝   papers. Works from CLI, web UI, or API.
         ▼
┌──────────────────┐   Extracts factual claims per paper in parallel
│  Reader Agent    │   batches. Every claim is stamped with
│                  │   paper_id + chunk_id + page IN CODE.
└────────┬─────────┘
         ▼
┌──────────────────┐   Local embeddings (MiniLM) group similar
│  Contradiction   │   claims for free; the LLM is spent only on
│  Agent           │   verdicts. Verdicts are cached on disk.
└────────┬─────────┘
         ▼
┌──────────────────┐   Code-assigned citation keys, conflicts surfaced
│  Writer Agent    │   first, quoted passages verified against the
└────────┬─────────┘   evidence, markdown report with references.
         ▼
   final_report.md
```

**Orchestration:** a LangGraph `StateGraph` with a shared typed state (`graph_state.py`). Each agent is a thin node wrapping core logic; the same functions also run standalone.

## Key Features

- **Contradiction detection:** cross-paper disagreement is actively identified and explained, then required reading for the Writer Agent so conflicts appear prominently in the report.
- **Human-in-the-loop by design:** the checkpoint is a LangGraph `interrupt()`. The graph freezes, control passes to an external decision-maker (CLI, frontend, or API), and execution resumes via `Command(resume=...)`.
- **End-to-end citation traceability:** chunk IDs stamped at extraction survive all five stages. The Writer cites `(Author, Year, p. X)` with an exact source chunk behind it.
- **Anti-hallucination checks:** citation keys are assigned in code, not by the LLM, and quoted passages are verified against the input evidence.
- **Cost-engineered:** local sentence-transformer embeddings handle retrieval (free, unlimited), and LLM calls are reserved for judgment. Caching at three layers (PDFs, per-paper claims, verdicts) makes repeat reviews nearly free.
- **Resilient:** exponential-backoff retries on transient LLM errors (429/503), a multi-source open-access PDF fallback, and keyword distillation with a fallback ladder for long natural-language questions.
- **Full API and frontend:** FastAPI exposes the pipeline, and the React frontend provides a live agent timeline, a streaming activity console, and a checkpoint approval screen.
- **Parallelized:** concurrent PDF downloads and claim extraction, sized to respect free-tier rate limits. Reference-section chunk pruning cuts LLM calls by roughly 40–60%.

## Tech Stack

| Layer | Tools |
|---|---|
| Agents and pipeline | Python, LangGraph (`StateGraph`, `interrupt` / `Command`) |
| LLM | Google Gemini (structured JSON output) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, local) |
| Paper search | Semantic Scholar API, Unpaywall, arXiv |
| PDF processing | PyMuPDF (page-tagged chunking) |
| API | FastAPI, Uvicorn, Pydantic |
| Frontend | React, Tailwind CSS |
| Persistence | SQLite (reviews + LangGraph checkpoints — survive restarts) |

## Getting Started

### Prerequisites

- Python 3.12+
- A Gemini API key (the free tier works): [aistudio.google.com](https://aistudio.google.com)
- *(Optional)* A Semantic Scholar API key

### Installation

```bash
git clone https://github.com/<your-username>/agentic-literature-review.git
cd agentic-literature-review
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

```env
# .env
GEMINI_API_KEY=your_gemini_key
S2_API_KEY=your_semantic_scholar_key     # optional
UNPAYWALL_EMAIL=you@example.com          # any real email (Unpaywall requirement)
```

### Run the pipeline (CLI)

```bash
python run_pipeline.py
# Enter a research question
# Watch the agents run and approve papers at the checkpoint
# final_report.md is written on completion
```

### Run the API and frontend

```bash
uvicorn api.main:app --reload
# API docs:  http://localhost:8000/docs
# Frontend:  http://localhost:8000  (or the React dev server)
```

## API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/reviews` | Start a review (runs in the background) |
| `GET` | `/reviews` | List all reviews |
| `GET` | `/reviews/{id}` | Review status, node status, and activity logs |
| `GET` | `/reviews/{id}/pending` | Checkpoint payload (ranked papers awaiting approval) |
| `POST` | `/reviews/{id}/decision` | Submit a decision: `approve_all`, `remove`, or `abort` |
| `POST` | `/reviews/{id}/retry` | Resume a failed review from its last checkpoint |
| `GET` | `/reviews/{id}/report` | Fetch the final markdown report |

### Example flow

```bash
# 1. Start a review
curl -X POST localhost:8000/reviews -H "Content-Type: application/json" \
  -d '{"query": "How does RAG reduce hallucination in LLMs?"}'

# 2. Poll until status == "awaiting_approval"
curl localhost:8000/reviews/rv-abc123

# 3. Inspect the ranked papers, then approve (or remove some)
curl -X POST localhost:8000/reviews/rv-abc123/decision \
  -H "Content-Type: application/json" -d '{"action": "approve_all"}'

# 4. Poll until "completed", then fetch the report
curl localhost:8000/reviews/rv-abc123/report
```

> The `interrupt()` checkpoint is the API boundary. The server never calls `input()`; the client decides over HTTP.

## Project Structure

```text
├── search_pipeline/        # Step 1: search, download (fallback chain), extract
│   ├── search.py           # Semantic Scholar search + keyword handling
│   ├── download.py         # PDF downloads: S2 → Unpaywall → arXiv, idempotent
│   └── extract.py          # PyMuPDF → page-tagged chunks with chunk_ids
├── filter_agent/           # Step 2: LLM relevance scoring
├── reader_agent/           # Step 3: claim extraction with full provenance
├── contradiction_agent/    # Step 4: local embeddings + LLM verdicts
├── writer_agent/           # Step 5: cited synthesis + verification
├── graph_state.py          # Shared LangGraph state schema
├── pipeline_graph.py       # The 6-node graph (5 agents + human checkpoint)
├── run_pipeline.py         # CLI entry point
├── api/                    # FastAPI layer + frontend
│   ├── main.py             # Endpoints
│   ├── review_store.py     # Review registry
│   └── pipeline_runner.py  # Background graph execution + resume               
├── LICENSE
└── README.md
```

## Design Decisions

- **Local embeddings for retrieval, LLM for reasoning.** Claim grouping uses a free local MiniLM model, and Gemini is spent only where judgment matters. This is a deliberate cost and latency split.
- **Provenance is stamped in code, never by the LLM.** Models read chunk IDs and write claims, but `paper_id`, `paper_title`, and citation keys are attached programmatically.
- **Fail loudly and early.** Zero search results, empty approvals, and missing API keys all raise immediately instead of flowing silently into downstream agents.
- **Caching everywhere.** PDFs are skipped if already on disk, and extracted claims and LLM verdicts are keyed by content hash, so re-runs and threshold tuning cost nothing.
- **Parallelism sized to rate limits.** Bounded worker pools (not maxed out) let free-tier quotas absorb the load, and the retry wrapper catches the rest.

## Limitations and Roadmap

### Known limitations

- Contradiction verdicts are LLM-judged (probabilistic), not formal logical checks.
- Claim grouping uses greedy leader-clustering, which is order-dependent. Centroid-based clustering is a future improvement.
- Only open-access papers are read in full. Paywalled papers are kept as abstract-only candidates, marked as such, and remain usable by the Filter Agent.

### Planned

- [ ] Resume-scan for interrupted reviews
- [ ] Per-review audit trail
- [ ] Evaluation harness (contradiction-detection precision against human labels)

## Acknowledgments

- [Semantic Scholar](https://www.semanticscholar.org/product/api) and [Unpaywall](https://unpaywall.org/products/api) for open research APIs
- [LangGraph](https://github.com/langchain-ai/langgraph) for interruptible agent orchestration
- Inspired by gaps observed in Elicit, Consensus, and similar tools

## License

This project is licensed under the [MIT License](LICENSE).

# 📚 Agentic Literature Review Assistant

> A human-in-the-loop, multi-agent AI system that takes a specific research question and produces a fully cited literature review — with explicit contradiction detection between papers and page-level citation traceability for every claim.

**Five specialized agents. One human checkpoint. Every claim grounded in an exact, traceable source passage.**

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-orchestration-1C3C3C)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎯 Why This Project Exists

Tools like Elicit, Consensus, and Paperguide retrieve and summarize papers, but they share real, documented weaknesses:

| Weakness in existing tools | How this project addresses it |
|---|---|
| ❌ No contradiction detection — disagreeing papers are silently blended | ⚔️ Dedicated **Contradiction Agent** groups claims by meaning and asks the LLM to judge *agree / conflict / unclear* — with an explanation of why |
| ❌ Fully autonomous — one bad early decision silently ruins the output | ✋ Explicit **human checkpoint** baked into the architecture (LangGraph `interrupt()`): approve/remove papers before the expensive reading step |
| ❌ Vague or fabricated citations | 🔗 **End-to-end provenance chain**: every claim carries `paper_id → chunk_id → page`, stamped in code (never trusted to the LLM), plus an anti-hallucination verification pass |
| ❌ Generic field surveys instead of answers | 🎯 Every stage is optimized toward answering **your specific question** — and honestly reports when evidence is sparse or one-sided |

---

## 🏗️ Architecture

```
 Research question
        │
        ▼
┌──────────────────┐   Semantic Scholar search (keyword-distilled),
│ 🔍 Search Agent  │   PDF download with fallback chain
│                  │   (S2 → Unpaywall → arXiv), page-tagged chunking
└────────┬─────────┘
         ▼
┌──────────────────┐   LLM scores each paper's relevance (1–10)
│ ⚖️ Filter Agent  │   with one-line reasons (native JSON mode)
└────────┬─────────┘
         ▼
╔══════════════════╗
║ ✋ HUMAN PAUSE    ║   LangGraph interrupt() — approve or remove
╚════════╤═════════╝   papers. Works from CLI, web UI, or API.
         ▼
┌──────────────────┐   Extracts factual claims per paper in parallel
│ 📖 Reader Agent  │   batches. Every claim is stamped with
│                  │   paper_id + chunk_id + page IN CODE.
└────────┬─────────┘
         ▼
┌──────────────────┐   Local embeddings (MiniLM) group similar
│ ⚔️ Contradiction │   claims for free; LLM is spent only on
│      Agent       │   verdicts. Verdicts cached on disk.
└────────┬─────────┘
         ▼
┌──────────────────┐   Code-assigned citation keys, conflicts surfaced
│ ✍️ Writer Agent  │   FIRST, quoted passages verified against the
└────────┬─────────┘   evidence, markdown report with references.
         ▼
   final_report.md
```

**Orchestration:** LangGraph `StateGraph` with a shared typed state (`graph_state.py`). Each agent is a thin node wrapping the core logic — the same functions also run standalone.

---

## 📸 Demo

<!-- Add a screenshot or GIF of the pipeline here, e.g.: -->
<!-- ![Demo](docs/demo.gif) -->

---

## ✨ Key Features

- ⚔️ **Contradiction detection** — cross-paper disagreement is actively hunted and explained, then required reading for the Writer Agent (conflicts appear prominently in the report)
- ✋ **Human-in-the-loop as architecture** — the checkpoint is a LangGraph `interrupt()`: the graph freezes, control passes to an external decision-maker (CLI / frontend / API), and resumes via `Command(resume=...)`
- 🔗 **Citation traceability end-to-end** — chunk IDs stamped at extraction survive all five stages; the Writer cites `(Author, Year, p. X)` with an exact source chunk behind it
- 🛡️ **Anti-hallucination checks** — citation keys assigned in code, not by the LLM; quoted passages verified against the input evidence
- 💸 **Cost-engineered** — local sentence-transformer embeddings for retrieval (free, unlimited), LLM calls reserved for judgment; caching at three layers (PDFs, per-paper claims, verdicts) makes repeat reviews nearly free
- 🧗 **Resilience** — retry with exponential backoff on transient LLM errors (429/503), multi-source open-access PDF fallback, keyword distillation + fallback ladder for long natural-language questions
- 🌐 **Full API + frontend** — FastAPI exposes the pipeline; the React frontend shows a live agent timeline, streaming activity console, and a checkpoint approval screen
- ⚡ **Parallelized** — concurrent PDF downloads and claim extraction, sized to respect free-tier rate limits; reference-section chunk pruning cuts LLM calls by ~40–60%

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| Agents & pipeline | Python, LangGraph (`StateGraph`, `interrupt`/`Command`) |
| LLM | Google Gemini (structured JSON output) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, local) |
| Paper search | Semantic Scholar API + Unpaywall + arXiv |
| PDF processing | PyMuPDF (page-tagged chunking) |
| API | FastAPI, Uvicorn, Pydantic |
| Frontend | React + Tailwind CSS (live pipeline visualization, checkpoint UI) |
| Persistence | In-memory store + LangGraph `MemorySaver` (SQLite drop-in planned) |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- A Gemini API key (free tier works) — [aistudio.google.com](https://aistudio.google.com)
- *(Optional)* Semantic Scholar API key

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
# → enter a research question
# → watch agents run, approve papers at the checkpoint
# → final_report.md is written
```

### Run the API + frontend

```bash
uvicorn api.main:app --reload
# API docs:  http://localhost:8000/docs
# Frontend:  http://localhost:8000  (or the React dev server)
```

---

## 🔌 API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/reviews` | Start a review (runs in background) |
| `GET` | `/reviews` | List all reviews |
| `GET` | `/reviews/{id}` | Review status + node status + activity logs |
| `GET` | `/reviews/{id}/pending` | Checkpoint payload (ranked papers awaiting approval) |
| `POST` | `/reviews/{id}/decision` | Submit decision: `approve_all` / `remove` / `abort` |
| `POST` | `/reviews/{id}/retry` | Resume a failed review from its last checkpoint |
| `GET` | `/reviews/{id}/report` | Final markdown report |

### Example flow

```bash
# 1. start
curl -X POST localhost:8000/reviews -H "Content-Type: application/json" \
  -d '{"query": "How does RAG reduce hallucination in LLMs?"}'

# 2. poll until status == "awaiting_approval"
curl localhost:8000/reviews/rv-abc123

# 3. inspect ranked papers, then approve (or remove some)
curl -X POST localhost:8000/reviews/rv-abc123/decision \
  -H "Content-Type: application/json" -d '{"action": "approve_all"}'

# 4. poll until "completed", then fetch the report
curl localhost:8000/reviews/rv-abc123/report
```

> The `interrupt()` checkpoint is the API boundary: the server never calls `input()` — the client decides, through HTTP.

---

## 📂 Project Structure

```
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
└── bruno/                  # API test collection (Bruno)
```

---

## ⚙️ Design Decisions Worth Knowing

- **Local embeddings for retrieval, LLM for reasoning** — grouping claims is done with a free local MiniLM model; Gemini is spent only where judgment matters. This is a deliberate cost/latency split.
- **Provenance is stamped in code, never by the LLM** — models are trusted to read chunk IDs and write claims, but `paper_id` / `paper_title` / citation keys are attached programmatically.
- **Fail loudly, early** — zero search results, empty approvals, and missing API keys all raise immediately instead of flowing silently into downstream agents.
- **Caching everywhere** — PDFs are skipped if on disk; extracted claims and LLM verdicts are keyed by content hash, so re-runs and threshold tuning cost nothing.
- **Parallelism sized to rate limits** — bounded worker pools (not maxed-out) so free-tier quotas absorb the load; the retry wrapper catches the rest.

---

## ⚠️ Limitations & Roadmap

- Review state and checkpoints are currently in-memory — a server restart loses paused reviews. (`ReviewStore` → SQLite table + `MemorySaver` → `SqliteSaver` are drop-in upgrades.)
- Contradiction verdicts are LLM-judged (probabilistic), not formal logical checks.
- Claim grouping uses greedy leader-clustering — order-dependent; centroid-based clustering is a future improvement.
- Open-access only: paywalled papers are kept as abstract-only candidates (marked honestly, still usable by the Filter Agent).
- **Planned:** SQLite persistence · resume-scan for interrupted reviews · per-review audit trail · evaluation harness (contradiction detection precision vs. human labels).

---

## 🙏 Acknowledgments

- [Semantic Scholar](https://www.semanticscholar.org/product/api) and [Unpaywall](https://unpaywall.org/products/api) for open research APIs
- [LangGraph](https://github.com/langchain-ai/langgraph) for interruptible agent orchestration
- Inspired by the gaps observed in Elicit, Consensus, and similar tools

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

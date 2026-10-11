import logging
import threading
from datetime import datetime, timezone

from langgraph.types import Command

from pipeline_graph import build_pipeline_graph
from api.review_store import store, Review

log = logging.getLogger(__name__)

_graph = None
_graph_lock = threading.Lock()


def _get_graph():
    global _graph
    if _graph is None:
        with _graph_lock:
            if _graph is None:
                from langgraph.checkpoint.memory import MemorySaver
                _graph = build_pipeline_graph(checkpointer=MemorySaver())
    return _graph


def start_review_thread(review_id: str, query: str) -> None:
    t = threading.Thread(
        target=_run_until_pause_or_end,
        args=(review_id, {"query": query}),
        daemon=True,
    )
    t.start()


def resume_review_thread(review_id: str, decision: dict) -> None:
    t = threading.Thread(
        target=_run_until_pause_or_end,
        args=(review_id, Command(resume=decision)),
        daemon=True,
    )
    t.start()


def _retry_review_thread(review_id: str) -> None:
    t = threading.Thread(
        target=_run_until_pause_or_end,
        args=(review_id, None),     # None input = continue, don't restart
        daemon=True,
    )
    t.start()    


def _run_until_pause_or_end(review_id: str, graph_input) -> None:
    review = store.get(review_id)
    if review is None:
        return

    config = {"configurable": {"thread_id": review.thread_id}}

    node_status = dict(getattr(review, "node_status", {}) or {})
    logs = list(getattr(review, "logs", []) or [])

    def add_log(agent: str, message: str):
        now = datetime.now(timezone.utc).strftime("%H:%M:%S")
        logs.append({"timestamp": now, "agent": agent, "message": message})

    if not logs:
        add_log("system", f"Review initiated for query: '{review.query[:60]}...'")
        node_status["search"] = {"status": "running", "summary": "Searching arXiv & Semantic Scholar..."}
        add_log("search", "Querying arXiv and Semantic Scholar APIs...")
        store.update(review_id, status="running", detail="Searching papers on arXiv & Semantic Scholar...", node_status=node_status, logs=logs)
    elif review.status == "awaiting_approval":
        node_status["human_checkpoint"] = {"status": "completed", "summary": "Approved papers confirmed"}
        node_status["reader"] = {"status": "running", "summary": "Extracting full-text claims..."}
        add_log("checkpoint", "Human decision recorded: resuming pipeline execution")
        add_log("reader", "Reading full-text PDFs and extracting evidence claims...")
        store.update(review_id, status="running", detail="Extracting claims from approved papers...", node_status=node_status, logs=logs)
    else:
        store.update(review_id, status="running", detail="Pipeline running.", node_status=node_status, logs=logs)

    interrupted = False
    interrupt_payload = {}
    report_path = None

    try:
        for event in _get_graph().stream(graph_input, config=config):
            for node_name, output in event.items():
                if node_name == "__interrupt__":
                    interrupted = True
                    interrupt_val = output[0].value if output and hasattr(output[0], 'value') else {}
                    interrupt_payload = interrupt_val if isinstance(interrupt_val, dict) else {}
                    node_status["human_checkpoint"] = {"status": "active", "summary": "Awaiting your paper approval"}
                    add_log("checkpoint", "Checkpoint reached: human approval required to proceed")
                    store.update(
                        review_id,
                        status="awaiting_approval",
                        detail=interrupt_payload.get("prompt", "Approval required."),
                        node_status=node_status,
                        logs=logs,
                    )
                    return
                elif node_name == "search":
                    papers = output.get("papers", [])
                    n_pdf = sum(1 for p in papers if p.get("pdf_status") == "downloaded")
                    node_status["search"] = {
                        "status": "completed",
                        "summary": f"{len(papers)} candidate papers found, {n_pdf} PDFs retrieved"
                    }
                    add_log("search", f"{len(papers)} candidates found on arXiv & Semantic Scholar ({n_pdf} full-text PDFs)")
                    node_status["filter"] = {"status": "running", "summary": "Scoring relevance with Gemini LLM..."}
                    add_log("filter", f"Scoring relevance for {len(papers)} papers against query...")
                    store.update(review_id, detail="Scoring paper relevance...", node_status=node_status, logs=logs)
                elif node_name == "filter":
                    papers = output.get("papers", [])
                    node_status["filter"] = {
                        "status": "completed",
                        "summary": f"Ranked {len(papers)} papers by relevance"
                    }
                    add_log("filter", f"Relevance ranking complete for {len(papers)} papers")
                    node_status["human_checkpoint"] = {"status": "active", "summary": "Awaiting your paper approval"}
                    store.update(review_id, detail="Approval required.", node_status=node_status, logs=logs)
                elif node_name == "human_checkpoint":
                    approved = output.get("approved_papers", [])
                    node_status["human_checkpoint"] = {
                        "status": "completed",
                        "summary": f"Approved {len(approved)} papers for review"
                    }
                    add_log("checkpoint", f"Human operator approved {len(approved)} papers")
                    node_status["reader"] = {"status": "running", "summary": "Extracting full-text claims..."}
                    add_log("reader", f"Extracting verifiable claims from {len(approved)} papers...")
                    store.update(review_id, detail="Extracting claims...", node_status=node_status, logs=logs)
                elif node_name == "reader":
                    approved = output.get("approved_papers", [])
                    total_claims = sum(len(p.get("claims", [])) for p in approved)
                    node_status["reader"] = {
                        "status": "completed",
                        "summary": f"Extracted {total_claims} claims across {len(approved)} papers"
                    }
                    add_log("reader", f"{total_claims} claims extracted and verified across {len(approved)} papers")
                    node_status["contradiction"] = {"status": "running", "summary": "Detecting cross-paper contradictions..."}
                    add_log("contradiction", "Clustering claim embeddings to check consensus & contradictions...")
                    store.update(review_id, detail="Checking contradictions...", node_status=node_status, logs=logs)
                elif node_name == "contradiction":
                    comparisons = output.get("comparisons", [])
                    conflicts = sum(1 for c in comparisons if c.get("verdict") == "conflict")
                    node_status["contradiction"] = {
                        "status": "completed",
                        "summary": f"{len(comparisons)} claim pairs analyzed ({conflicts} conflicts detected)"
                    }
                    add_log("contradiction", f"Cross-paper consensus analysis: {len(comparisons)} pairs checked, {conflicts} conflict(s)")
                    node_status["writer"] = {"status": "running", "summary": "Synthesizing cited academic report..."}
                    add_log("writer", "Synthesizing literature review with verified citation keys...")
                    store.update(review_id, detail="Synthesizing final report...", node_status=node_status, logs=logs)
                elif node_name == "writer":
                    report_path = output.get("report_path")
                    node_status["writer"] = {
                        "status": "completed",
                        "summary": "Literature review synthesized and verified"
                    }
                    add_log("writer", "Literature review synthesized with inline citations")
                    add_log("system", "Pipeline complete. Final report ready.")
    except Exception as e:
        log.exception("Review %s failed", review_id)
        add_log("system", f"Pipeline error: {str(e)}")
        store.update(review_id, status="failed", detail=str(e), node_status=node_status, logs=logs)
        return

    if not interrupted:
        # Check if report_path is in state if writer didn't yield it
        if not report_path:
            state = _get_graph().get_state(config)
            report_path = state.values.get("report_path")

        store.update(
            review_id,
            status="completed",
            report_path=report_path,
            detail="Done.",
            node_status=node_status,
            logs=logs,
        )

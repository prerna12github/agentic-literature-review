import logging
import threading

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
    store.update(review_id, status="running", detail="Pipeline running.")

    try:
        result = _get_graph().invoke(graph_input, config=config)
    except Exception as e:
        log.exception("Review %s failed", review_id)
        store.update(review_id, status="failed", detail=str(e))
        return

    if "__interrupt__" in result:
       
        payload = result["__interrupt__"][0].value
        store.update(
            review_id,
            status="awaiting_approval",
            detail=payload.get("prompt", "Approval required."),
        )
    else:
        store.update(
            review_id,
            status="completed",
            report_path=result.get("report_path"),
            detail="Done.",
        )
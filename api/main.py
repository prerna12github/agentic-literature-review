import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from api.review_store import store
from api.pipeline_runner import start_review_thread, resume_review_thread

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from api.pipeline_runner import _get_graph
    _get_graph()
    log.info("Pipeline graph compiled and ready.")
    yield


app = FastAPI(
    title="Agentic Literature Review API",
    description="Human-in-the-loop literature review pipeline: "
                "search → filter → [human approval] → read → "
                "contradiction-check → write.",
    version="1.0.0",
    lifespan=lifespan,
)


# --------------------------------------------------------------------------
# Request / response models
# --------------------------------------------------------------------------
class ReviewRequest(BaseModel):
    query: str = Field(..., min_length=10,
                       description="The research question")


class DecisionRequest(BaseModel):
    action: str = Field(..., pattern="^(approve_all|remove|abort)$")
    remove: list[int] = Field(
        default=[],
        description="Indices to remove (only for action='remove')",
    )


class ReviewOut(BaseModel):
    review_id: str
    query: str
    status: str
    detail: str
    report_path: str | None = None
    created_at: str


def _review_or_404(review_id: str):
    review = store.get(review_id)
    if review is None:
        raise HTTPException(404, f"Review '{review_id}' not found")
    return review


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------
@app.post("/reviews", response_model=ReviewOut, status_code=201)
def create_review(req: ReviewRequest):
    review = store.create(req.query)
    start_review_thread(review.review_id, req.query)
    return review


@app.get("/reviews", response_model=list[ReviewOut])
def list_reviews():
    return store.all()


@app.get("/reviews/{review_id}", response_model=ReviewOut)
def get_review(review_id: str):
    return _review_or_404(review_id)


@app.get("/reviews/{review_id}/pending")
def get_pending(review_id: str):
    review = _review_or_404(review_id)

    if review.status != "awaiting_approval":
        raise HTTPException(
            409,
            f"Review is '{review.status}', not 'awaiting_approval'. "
            "Poll GET /reviews/{id} until the checkpoint is reached.",
        )

    from api.pipeline_runner import _get_graph
    config = {"configurable": {"thread_id": review.thread_id}}
    state = _get_graph().get_state(config)

    ranked = sorted(
        state.values.get("papers", []),
        key=lambda p: p.get("relevance_score", 0),
        reverse=True,
    )

    return {
        "review_id": review_id,
        "prompt": "Approve papers for full reading?",
        "papers": [
            {
                "index": i,
                "title": p.get("title"),
                "year": p.get("year"),
                "score": p.get("relevance_score"),
                "reason": p.get("relevance_reason"),
                "pdf_status": p.get("pdf_status"),
            }
            for i, p in enumerate(ranked)
        ],
    }


@app.post("/reviews/{review_id}/decision", response_model=ReviewOut)
def submit_decision(review_id: str, req: DecisionRequest):
    review = _review_or_404(review_id)

    if review.status != "awaiting_approval":
        raise HTTPException(
            409,
            f"Review is '{review.status}' — nothing is awaiting approval.",
        )

    if req.action == "abort":
        store.update(review_id, status="aborted",
                     detail="Aborted by human at checkpoint.")
        return review

    if req.action == "remove" and not req.remove:
        raise HTTPException(422, "action='remove' requires 'remove' indices")

    decision = (
        {"action": "approve_all"}
        if req.action == "approve_all"
        else {"action": "remove", "remove": req.remove}
    )

    store.update(review_id, status="running", detail="Resumed by human.")
    resume_review_thread(review_id, decision)
    return store.get(review_id)


@app.get("/reviews/{review_id}/report", response_class=PlainTextResponse)
def get_report(review_id: str):
    review = _review_or_404(review_id)

    if review.status != "completed":
        raise HTTPException(
            409, f"Review is '{review.status}' — no report yet."
        )

    with open(review.report_path, "r") as f:
        return PlainTextResponse(f.read(), media_type="text/markdown")
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Review:
    review_id: str
    thread_id: str
    query: str
    status: str = "starting"          
    detail: str = ""                 
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    report_path: str | None = None
    node_status: dict[str, Any] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)


class ReviewStore:
    def __init__(self):
        self._reviews: dict[str, Review] = {}
        self._lock = threading.Lock()

    def create(self, query: str) -> Review:
        review = Review(
            review_id=f"rv-{uuid.uuid4().hex[:8]}",
            thread_id=f"thread-{uuid.uuid4().hex[:12]}",
            query=query,
        )
        with self._lock:
            self._reviews[review.review_id] = review
        return review

    def get(self, review_id: str) -> Review | None:
        with self._lock:
            return self._reviews.get(review_id)

    def all(self) -> list[Review]:
        with self._lock:
            return list(self._reviews.values())

    def update(self, review_id: str, **fields) -> Review | None:
        with self._lock:
            review = self._reviews.get(review_id)
            if review is None:
                return None
            for k, v in fields.items():
                setattr(review, k, v)
            return review

store = ReviewStore()

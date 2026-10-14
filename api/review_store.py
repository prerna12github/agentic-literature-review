import sqlite3
import threading
import uuid
from datetime import datetime

DB_FILE = "reviews.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id   TEXT PRIMARY KEY,
    thread_id   TEXT NOT NULL,
    query       TEXT NOT NULL,
    status      TEXT NOT NULL,
    detail      TEXT DEFAULT '',
    report_path TEXT,
    created_at  TEXT NOT NULL
)
"""


class ReviewStore:
    def __init__(self, db_file: str = DB_FILE):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_file, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def _to_review(self, row) -> dict:
        return {
            "review_id": row["review_id"],
            "thread_id": row["thread_id"],
            "query": row["query"],
            "status": row["status"],
            "detail": row["detail"],
            "report_path": row["report_path"],
            "created_at": row["created_at"],
        }

    def create(self, query: str) -> dict:
        review = {
            "review_id": f"rv-{uuid.uuid4().hex[:8]}",
            "thread_id": f"thread-{uuid.uuid4().hex[:12]}",
            "query": query,
            "status": "starting",
            "detail": "",
            "report_path": None,
            "created_at": datetime.utcnow().isoformat(),
        }
        with self._lock:
            self._conn.execute(
                "INSERT INTO reviews VALUES (:review_id, :thread_id, :query, "
                ":status, :detail, :report_path, :created_at)",
                review,
            )
            self._conn.commit()
        return review

    def get(self, review_id: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM reviews WHERE review_id = ?", (review_id,)
            ).fetchone()
        return self._to_review(row) if row else None

    def all(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM reviews ORDER BY created_at DESC"
            ).fetchall()
        return [self._to_review(r) for r in rows]

    def update(self, review_id: str, **fields) -> dict | None:
        allowed = {"status", "detail", "report_path"}
        bad = [k for k in fields if k not in allowed]
        if bad:
            raise ValueError(f"Cannot update fields: {bad}")
        sets = ", ".join(f"{k} = :{k}" for k in fields)
        with self._lock:
            self._conn.execute(
                f"UPDATE reviews SET {sets} WHERE review_id = :rid",
                {**fields, "rid": review_id},
            )
            self._conn.commit()
        return self.get(review_id)

store = ReviewStore()
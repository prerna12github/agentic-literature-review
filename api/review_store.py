import json
import sqlite3
import threading
import uuid
from datetime import datetime
from types import SimpleNamespace

DB_FILE = "reviews.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id   TEXT PRIMARY KEY,
    thread_id   TEXT NOT NULL,
    query       TEXT NOT NULL,
    status      TEXT NOT NULL,
    detail      TEXT DEFAULT '',
    report_path TEXT,
    created_at  TEXT NOT NULL,
    node_status TEXT DEFAULT '{}',
    logs        TEXT DEFAULT '[]'
)
"""


class ReviewStore:
    def __init__(self, db_file: str = DB_FILE):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_file, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    def _to_review(self, row) -> SimpleNamespace:
      data = {k: row[k] for k in row.keys()}
      data["node_status"] = json.loads(data.get("node_status") or "{}")
      data["logs"] = json.loads(data.get("logs") or "[]")
      return SimpleNamespace(**data)

    def create(self, query: str) -> SimpleNamespace:
     review = {
        "review_id": f"rv-{uuid.uuid4().hex[:8]}",
        "thread_id": f"thread-{uuid.uuid4().hex[:12]}",
        "query": query,
        "status": "starting",
        "detail": "",
        "report_path": None,
        "created_at": datetime.utcnow().isoformat(),
        "node_status": {},   # real dict internally
        "logs": [],          # real list internally
    }
    # serialize ONLY for storage
     params = {
        **review,
        "node_status": json.dumps(review["node_status"]),
        "logs": json.dumps(review["logs"]),
    }
     with self._lock:
        self._conn.execute(
            """INSERT INTO reviews
               (review_id, thread_id, query, status, detail,
                report_path, created_at, node_status, logs)
               VALUES (:review_id, :thread_id, :query, :status, :detail,
                       :report_path, :created_at, :node_status, :logs)""",
            params,
        )
        self._conn.commit()
     return SimpleNamespace(**review)   

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

    def update(self, review_id: str, **fields) -> SimpleNamespace | None:
     allowed = {"status", "detail", "report_path", "node_status", "logs"}
     bad = [k for k in fields if k not in allowed]
     if bad:
        raise ValueError(f"Cannot update fields: {bad}")
     if "node_status" in fields and not isinstance(fields["node_status"], str):
        fields["node_status"] = json.dumps(fields["node_status"])
     if "logs" in fields and not isinstance(fields["logs"], str):
        fields["logs"] = json.dumps(fields["logs"])

     sets = ", ".join(f"{k} = :{k}" for k in fields)
     with self._lock:
        self._conn.execute(
            f"UPDATE reviews SET {sets} WHERE review_id = :rid",
            {**fields, "rid": review_id},
        )
        self._conn.commit()
     return self.get(review_id)

store = ReviewStore()
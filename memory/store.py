"""SQLite-backed memory store with type discrimination.

Single store: working | episodic | semantic. Persistence across requests;
read/write by agents. Working memory is session-scoped; pruning in working_memory.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from memory.models import MemoryRecord, MemoryType

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path("data/memory.db")
TABLE_NAME = "memories"


def _row_to_record(row: tuple) -> MemoryRecord:
    id_, type_, session_id, content, metadata_json, created_at, updated_at = row
    metadata = json.loads(metadata_json) if metadata_json else {}
    return MemoryRecord(
        id=id_,
        type=type_,
        session_id=session_id,
        content=content,
        metadata=metadata,
        created_at=datetime_from_iso(created_at),
        updated_at=datetime_from_iso(updated_at),
    )


def datetime_from_iso(s: str | None) -> Any:
    from datetime import datetime
    if s is None:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()


class MemoryStore:
    """Persistent memory store (SQLite) with type and optional session_id."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self._path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL CHECK (type IN ('working', 'episodic', 'semantic')),
                    session_id TEXT,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_memories_type_session "
                f"ON {TABLE_NAME} (type, session_id)"
            )
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_memories_created "
                f"ON {TABLE_NAME} (created_at)"
            )

    def create(
        self,
        type_: MemoryType,
        content: str,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        id_: str | None = None,
    ) -> MemoryRecord:
        """Insert a memory and return the record."""
        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"
        rid = id_ or str(uuid.uuid4())
        meta = json.dumps(metadata or {})
        with self._conn() as conn:
            conn.execute(
                f"INSERT INTO {TABLE_NAME} (id, type, session_id, content, metadata, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (rid, type_, session_id, content, meta, now, now),
            )
        logger.info("Memory created id=%s type=%s session_id=%s", rid, type_, session_id)
        return self.get(rid)

    def get(self, id_: str) -> MemoryRecord | None:
        """Return a memory by id or None."""
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT id, type, session_id, content, metadata, created_at, updated_at FROM {TABLE_NAME} WHERE id = ?",
                (id_,),
            ).fetchone()
        if row is None:
            return None
        return _row_to_record(tuple(row))

    def list(
        self,
        type_: MemoryType | None = None,
        session_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MemoryRecord]:
        """List memories with optional filters. Ordered by created_at desc."""
        with self._conn() as conn:
            q = f"SELECT id, type, session_id, content, metadata, created_at, updated_at FROM {TABLE_NAME}"
            params: list[Any] = []
            if type_ is not None:
                q += " WHERE type = ?"
                params.append(type_)
            if session_id is not None:
                q += " AND session_id = ?" if "WHERE" in q else " WHERE session_id = ?"
                params.append(session_id)
            q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            rows = conn.execute(q, params).fetchall()
        return [_row_to_record(tuple(r)) for r in rows]

    def update(self, id_: str, content: str | None = None, metadata: dict[str, Any] | None = None) -> MemoryRecord | None:
        """Update content and/or metadata. Returns updated record or None."""
        from datetime import datetime
        rec = self.get(id_)
        if rec is None:
            return None
        updates = []
        params: list[Any] = []
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))
        if not updates:
            return rec
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat() + "Z")
        params.append(id_)
        with self._conn() as conn:
            conn.execute(
                f"UPDATE {TABLE_NAME} SET " + ", ".join(updates) + " WHERE id = ?",
                params,
            )
        logger.info("Memory updated id=%s", id_)
        return self.get(id_)

    def delete(self, id_: str) -> bool:
        """Delete a memory by id. Returns True if deleted."""
        with self._conn() as conn:
            cur = conn.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?", (id_,))
            deleted = cur.rowcount > 0
        if deleted:
            logger.info("Memory deleted id=%s", id_)
        return deleted

    def delete_by_session(self, session_id: str, type_: MemoryType = "working") -> int:
        """Delete all memories for a session (e.g. working memory). Returns count."""
        with self._conn() as conn:
            cur = conn.execute(
                f"DELETE FROM {TABLE_NAME} WHERE session_id = ? AND type = ?",
                (session_id, type_),
            )
            n = cur.rowcount
        if n:
            logger.info("Memories deleted session_id=%s type=%s count=%d", session_id, type_, n)
        return n

    def list_sessions(
        self,
        type_: MemoryType = "working",
        limit: int = 100,
    ) -> list[tuple[str, str]]:
        """List distinct session_ids with optional type filter. Returns (session_id, latest_created_at)."""
        with self._conn() as conn:
            rows = conn.execute(
                f"""
                SELECT session_id, MAX(created_at) AS latest
                FROM {TABLE_NAME}
                WHERE type = ? AND session_id IS NOT NULL AND session_id != ''
                GROUP BY session_id
                ORDER BY latest DESC
                LIMIT ?
                """,
                (type_, limit),
            ).fetchall()
        return [(r[0], r[1]) for r in rows]

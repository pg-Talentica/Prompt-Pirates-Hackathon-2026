"""Service layer for memory: list, get, update, delete.

Used by the Memory Agent and by the backend API (Task-008) for the memory UI
(list, edit, delete). Agents read/write via store or working_memory; UI uses service.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from memory.models import MemoryCreate, MemoryRecord, MemoryUpdate, MemoryType
from memory.store import DEFAULT_DB_PATH, MemoryStore

logger = logging.getLogger(__name__)


class MemoryService:
    """Backend service for memory CRUD (list, get, update, delete)."""

    def __init__(self, store: MemoryStore | None = None, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self._store = store or MemoryStore(db_path=db_path)

    def list_memories(
        self,
        type_: MemoryType | None = None,
        session_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List memories with optional filters. Returns list of dicts for API/UI."""
        records = self._store.list(type_=type_, session_id=session_id, limit=limit, offset=offset)
        return [_record_to_dict(r) for r in records]

    def get_memory(self, id_: str) -> dict[str, Any] | None:
        """Get a memory by id. Returns dict or None."""
        rec = self._store.get(id_)
        return _record_to_dict(rec) if rec else None

    def create_memory(self, payload: MemoryCreate) -> dict[str, Any]:
        """Create a memory. Returns created record as dict."""
        rec = self._store.create(
            type_=payload.type,
            content=payload.content,
            session_id=payload.session_id,
            metadata=payload.metadata,
        )
        return _record_to_dict(rec)

    def update_memory(self, id_: str, payload: MemoryUpdate) -> dict[str, Any] | None:
        """Update content and/or metadata. Returns updated record or None."""
        rec = self._store.update(
            id_,
            content=payload.content,
            metadata=payload.metadata,
        )
        return _record_to_dict(rec) if rec else None

    def delete_memory(self, id_: str) -> bool:
        """Delete a memory by id. Returns True if deleted."""
        return self._store.delete(id_)


def _record_to_dict(r: MemoryRecord) -> dict[str, Any]:
    return {
        "id": r.id,
        "type": r.type,
        "session_id": r.session_id,
        "content": r.content,
        "metadata": r.metadata,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def get_memory_service(db_path: Path | str | None = None) -> MemoryService:
    """Return a MemoryService instance (for API dependency injection)."""
    return MemoryService(db_path=db_path or DEFAULT_DB_PATH)

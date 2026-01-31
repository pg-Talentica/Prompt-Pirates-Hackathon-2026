"""Memory read/write tools for agents (Memory Agent and others).

Wraps memory store (Task-004) with observable logging. Agents call these;
tools do the work; agents decide when to call.
"""

from __future__ import annotations

from typing import Any

from memory.models import MemoryType
from memory.service import get_memory_service
from memory.store import DEFAULT_DB_PATH, MemoryStore
from memory.working_memory import add_working, get_working
from tools.observability import wrap_tool


def _get_store() -> MemoryStore:
    return MemoryStore(db_path=DEFAULT_DB_PATH)


def memory_read(
    session_id: str | None = None,
    type_: MemoryType | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Read memories: list by type and/or session_id. Returns list of memory dicts."""
    svc = get_memory_service()
    records = svc.list_memories(type_=type_, session_id=session_id, limit=limit, offset=offset)
    return records


def memory_read_working(session_id: str, limit: int = 30) -> list[tuple[str, str]]:
    """Read working memory for a session as (role, content) pairs. Used by agents for context."""
    store = _get_store()
    return get_working(store, session_id, limit=limit)


def memory_write(
    type_: MemoryType,
    content: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write a memory (episodic or semantic). Returns created record as dict."""
    from memory.models import MemoryCreate
    svc = get_memory_service()
    payload = MemoryCreate(type=type_, content=content, session_id=session_id, metadata=metadata or {})
    return svc.create_memory(payload)


def memory_write_working(session_id: str, role: str, content: str) -> dict[str, Any]:
    """Append a message to working memory for the session. Returns created record as dict."""
    store = _get_store()
    rec = add_working(store, session_id, role, content)
    return {
        "id": rec.id,
        "type": "working",
        "session_id": session_id,
        "content": rec.content,
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
    }


# Observable-wrapped tools for agents (log input, execution, result)
memory_read_tool = wrap_tool("memory_read", memory_read)
memory_read_working_tool = wrap_tool("memory_read_working", memory_read_working)
memory_write_tool = wrap_tool("memory_write", memory_write)
memory_write_working_tool = wrap_tool("memory_write_working", memory_write_working)

"""Session-scoped working memory with pruning for long threads.

Working memory is short-lived, per session/thread. When the number of items
exceeds a threshold, oldest items are pruned (windowing) to prevent unbounded
growth. Optional summarization can be wired by agents (Task-007).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from memory.models import MemoryRecord
from memory.store import MemoryStore

logger = logging.getLogger(__name__)

DEFAULT_MAX_WORKING_ITEMS = 30
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_SYSTEM = "system"


def _message_content(role: str, content: str) -> str:
    """Store a single message as JSON for working memory."""
    return json.dumps({"role": role, "content": content})


def _parse_message(content: str) -> tuple[str, str]:
    """Parse stored message to (role, content)."""
    try:
        d = json.loads(content)
        return (d.get("role", "user"), d.get("content", content))
    except Exception:
        return ("user", content)


def add_working(
    store: MemoryStore,
    session_id: str,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
    max_items: int = DEFAULT_MAX_WORKING_ITEMS,
) -> MemoryRecord:
    """Append a message to working memory for the session, then prune if over max_items."""
    msg = _message_content(role, content)
    meta = metadata or {}
    meta["role"] = role
    rec = store.create(
        type_="working",
        content=msg,
        session_id=session_id,
        metadata=meta,
    )
    prune_working(store, session_id, max_items=max_items)
    return rec


def get_working(
    store: MemoryStore,
    session_id: str,
    limit: int = DEFAULT_MAX_WORKING_ITEMS,
) -> list[tuple[str, str]]:
    """Return recent working memory messages for the session as (role, content), newest last."""
    records = store.list(type_="working", session_id=session_id, limit=limit, offset=0)
    # list() returns created_at DESC, so reverse to get chronological order
    out = []
    for r in reversed(records):
        role, content = _parse_message(r.content)
        out.append((role, content))
    return out


def prune_working(
    store: MemoryStore,
    session_id: str,
    max_items: int = DEFAULT_MAX_WORKING_ITEMS,
) -> int:
    """Keep only the most recent max_items working memories for the session; delete older. Returns count deleted."""
    records = store.list(type_="working", session_id=session_id, limit=9999, offset=0)
    if len(records) <= max_items:
        return 0
    # records are created_at DESC, so records[max_items:] are the oldest
    to_delete = records[max_items:]
    deleted = 0
    for r in to_delete:
        if store.delete(r.id):
            deleted += 1
    if deleted:
        logger.info("Pruned working memory session_id=%s deleted=%d kept=%d", session_id, deleted, max_items)
    return deleted


def get_working_as_context(store: MemoryStore, session_id: str, limit: int = DEFAULT_MAX_WORKING_ITEMS) -> str:
    """Return working memory formatted as a single context string for agents (e.g. for prompt)."""
    messages = get_working(store, session_id, limit=limit)
    parts = []
    for role, content in messages:
        parts.append(f"{role}: {content}")
    return "\n".join(parts) if parts else ""

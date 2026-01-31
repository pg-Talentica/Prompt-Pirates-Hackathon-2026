"""Session/thread list for working memory and long-chat support.

Sessions are client-provided IDs; this endpoint lists session_ids that have
working memory in the store (no external ticket system).
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from memory.store import MemoryStore

router = APIRouter(prefix="/sessions", tags=["Sessions"])


class SessionItem(BaseModel):
    """A session that has working memory."""

    session_id: str = Field(..., description="Session/thread id")
    latest_activity: str = Field(..., description="ISO timestamp of latest activity")


class SessionsResponse(BaseModel):
    """List of sessions with working memory."""

    sessions: list[SessionItem] = Field(default_factory=list)


@router.get("", response_model=SessionsResponse)
async def list_sessions(limit: int = 100):
    """List session_ids that have working memory. For multi-turn and long-chat support."""
    store = MemoryStore()
    rows = store.list_sessions(type_="working", limit=limit)
    return SessionsResponse(
        sessions=[
            SessionItem(session_id=sid, latest_activity=latest)
            for sid, latest in rows
        ],
    )

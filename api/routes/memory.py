"""Memory CRUD API for the UI (list, get, update, delete)."""

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query

from memory.models import MemoryCreate, MemoryUpdate
from memory.service import get_memory_service

router = APIRouter(prefix="/memories", tags=["Memory"])


MemoryTypeQuery = Literal["working", "episodic", "semantic"]


@router.get("")
async def list_memories(
    type_: Optional[MemoryTypeQuery] = Query(None, alias="type"),
    session_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """List memories with optional filters (type, session_id). For UI and agents."""
    svc = get_memory_service()
    return svc.list_memories(type_=type_, session_id=session_id, limit=limit, offset=offset)


@router.get("/{memory_id}")
async def get_memory(memory_id: str):
    """Get a memory by id."""
    svc = get_memory_service()
    rec = svc.get_memory(memory_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return rec


@router.post("")
async def create_memory(payload: MemoryCreate):
    """Create a memory (for agents or UI)."""
    svc = get_memory_service()
    return svc.create_memory(payload)


@router.patch("/{memory_id}")
async def update_memory(memory_id: str, payload: MemoryUpdate):
    """Update content and/or metadata. For UI edit."""
    svc = get_memory_service()
    rec = svc.update_memory(memory_id, payload)
    if rec is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return rec


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a memory by id. For UI delete."""
    svc = get_memory_service()
    if not svc.delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": memory_id}

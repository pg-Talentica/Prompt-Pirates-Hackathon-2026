"""Pydantic models for memory records.

Single store with type: working | episodic | semantic.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

MemoryType = Literal["working", "episodic", "semantic"]


class MemoryRecord(BaseModel):
    """A single memory entry with type and optional session scope."""

    id: str
    type: MemoryType = Field(..., description="working | episodic | semantic")
    session_id: str | None = Field(default=None, description="Required for working; optional for others")
    content: str = Field(..., description="Text or JSON content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"extra": "forbid"}


class MemoryCreate(BaseModel):
    """Payload for creating a memory."""

    type: MemoryType
    session_id: str | None = None
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryUpdate(BaseModel):
    """Payload for updating a memory (partial)."""

    content: str | None = None
    metadata: dict[str, Any] | None = None

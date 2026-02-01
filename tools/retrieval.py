"""Retrieval tool for RAG: query the knowledge base and return relevant context with source refs.

This module implements **retrieval only**. Reasoning and response synthesis are
handled by separate agents (Task-007); retrieval always happens before generation
when the KB is used.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from tools.observability import wrap_tool
from tools.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Default persist path; can be overridden by env or caller
DEFAULT_PERSIST_DIR = "data/vector_store"


def get_vector_store(
    persist_directory: str | Path = DEFAULT_PERSIST_DIR,
    api_key: str | None = None,
) -> VectorStore:
    """Return a VectorStore instance (uses LLM_API_KEY from env if api_key not passed)."""
    if api_key is None:
        try:
            from api.config import get_settings
            api_key = get_settings().llm_api_key or None
        except Exception:
            api_key = None
    return VectorStore(persist_directory=persist_directory, api_key=api_key)


def retrieve(
    query: str,
    k: int = 5,
    persist_directory: str | Path = DEFAULT_PERSIST_DIR,
    api_key: str | None = None,
    max_distance: float | None = None,
) -> list[dict[str, Any]]:
    """Retrieve top-k relevant chunks for a query, with source references.

    Returns a list of dicts with keys: text, source_file, chunk_index, start, end, distance.
    Results with distance > max_distance are discarded (out-of-context filtering).
    """
    if max_distance is None:
        try:
            from api.config import get_settings
            max_distance = get_settings().rag_max_distance
        except Exception:
            max_distance = 1.2
    store = get_vector_store(persist_directory=persist_directory, api_key=api_key)
    results = store.search(query=query, k=k)
    
    # Log raw results before filtering
    if results:
        raw_distances = [r.get("distance") for r in results if r.get("distance") is not None]
        if raw_distances:
            logger.debug("Raw retrieval distances: min=%.4f, max=%.4f", min(raw_distances), max(raw_distances))
    
    # Filter by relevance: discard chunks with distance > max_distance (L2; lower = better)
    filtered = []
    for r in results:
        d = r.get("distance")
        if d is None:
            filtered.append(r)  # No distance = keep (e.g. some backends)
        elif d <= max_distance:
            filtered.append(r)
        else:
            logger.debug("Filtered out result with distance %.4f > %.2f", d, max_distance)
    
    logger.info("Retrieval query=%r k=%d -> %d results (after relevance filter, max_distance=%.2f)", 
               query[:50], k, len(filtered), max_distance)
    return filtered


def _retrieval_tool_impl(query: str, k: int = 5) -> list[dict[str, Any]]:
    """Internal: retrieve with defaults (no observability)."""
    return retrieve(query=query, k=k)


# Observable-wrapped tool for agents (logs input, execution, result; streamable to UI)
retrieval_tool = wrap_tool("retrieval", _retrieval_tool_impl)


def retrieval_tool_raw(query: str, k: int = 5) -> list[dict[str, Any]]:
    """Retrieve without observability (e.g. for tests). Same as retrieve(query, k)."""
    return retrieve(query=query, k=k)

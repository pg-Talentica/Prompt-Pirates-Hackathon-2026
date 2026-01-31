"""Chunking configuration for the knowledge-base corpus.

Used by the RAG pipeline (Task-003) to split documents into chunks with overlap.
All values are documented and justified in the main README (Chunking strategy).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class Chunk(TypedDict):
    """A single chunk of text with bounds."""

    text: str
    start: int
    end: int


@dataclass(frozen=True)
class ChunkingConfig:
    """Character-based chunk size and overlap for document splitting."""

    # Chunk size in characters (~200–250 tokens at ~4 chars/token)
    chunk_size: int = 800
    # Overlap in characters to preserve semantic continuity across boundaries
    overlap_size: int = 100

    def __post_init__(self) -> None:
        if self.overlap_size >= self.chunk_size:
            raise ValueError("overlap_size must be less than chunk_size")
        if self.chunk_size < 100:
            raise ValueError("chunk_size must be at least 100")

    @property
    def step(self) -> int:
        """Character step between chunk starts (chunk_size - overlap)."""
        return self.chunk_size - self.overlap_size


# Default config used by indexing and retrieval (defined before chunk_text)
DEFAULT_CHUNKING = ChunkingConfig()


def chunk_text(text: str, config: ChunkingConfig | None = None) -> list[Chunk]:
    """Split text into overlapping chunks using config.

    Uses a sliding window: each chunk is config.chunk_size chars; consecutive
    chunks overlap by config.overlap_size. Yields chunks with start/end indices.
    """
    cfg = config or DEFAULT_CHUNKING
    chunks: list[Chunk] = []
    start = 0
    while start < len(text):
        end = min(start + cfg.chunk_size, len(text))
        chunk_text_str = text[start:end]
        if chunk_text_str.strip():
            chunks.append(Chunk(text=chunk_text_str, start=start, end=end))
        start += cfg.step
        if start < len(text) and end == len(text):
            break
    return chunks

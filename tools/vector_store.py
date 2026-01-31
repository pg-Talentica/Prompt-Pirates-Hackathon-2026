"""Persistent vector store for RAG: index chunks and search by similarity.

Uses Chroma for storage and OpenAI for embeddings. Indexing and retrieval
use the chunking config from data.chunking.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from data.chunking import DEFAULT_CHUNKING, Chunk, ChunkingConfig, chunk_text

logger = logging.getLogger(__name__)

COLLECTION_NAME = "support_co_pilot_kb"


def _get_embedding_function(api_key: str | None = None):
    """Return a Chroma-compatible embedding function (OpenAI or fallback)."""
    try:
        from chromadb.utils import embedding_functions as ef
    except ImportError:
        raise ImportError("Install chromadb: pip install chromadb") from None

    if api_key and api_key.strip():
        return ef.OpenAIEmbeddingFunction(
            api_key=api_key.strip(),
            model_name="text-embedding-3-small",
        )
    try:
        return ef.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    except Exception as e:
        logger.warning("SentenceTransformer fallback failed: %s", e)
        raise ValueError(
            "Set LLM_API_KEY for OpenAI embeddings, or install sentence-transformers for local embeddings."
        ) from e


class VectorStore:
    """Persistent vector store for document chunks (Chroma + OpenAI embeddings)."""

    def __init__(
        self,
        persist_directory: str | Path = "data/vector_store",
        api_key: str | None = None,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self._path = Path(persist_directory)
        self._path.mkdir(parents=True, exist_ok=True)
        self._api_key = api_key
        self._collection_name = collection_name
        self._client = None
        self._collection = None

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        try:
            import chromadb
        except ImportError:
            raise ImportError("Install chromadb: pip install chromadb") from None
        self._client = chromadb.PersistentClient(path=str(self._path))
        emb_fn = _get_embedding_function(self._api_key)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            embedding_function=emb_fn,
            metadata={"description": "KB chunks for Support Co-Pilot RAG"},
        )

    def add_document(
        self,
        source_file: str,
        text: str,
        config: ChunkingConfig | None = None,
    ) -> int:
        """Chunk a document and add chunks to the store. Returns number of chunks added."""
        self._ensure_client()
        cfg = config or DEFAULT_CHUNKING
        chunks = chunk_text(text, cfg)
        if not chunks:
            return 0
        ids = []
        documents = []
        metadatas = []
        for i, c in enumerate(chunks):
            chunk_id = _chunk_id(source_file, i)
            ids.append(chunk_id)
            documents.append(c["text"])
            metadatas.append({
                "source_file": source_file,
                "chunk_index": i,
                "start": c["start"],
                "end": c["end"],
            })
        self._collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("Added %s: %d chunks", source_file, len(chunks))
        return len(chunks)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Return top-k chunks most similar to query, with source refs."""
        self._ensure_client()
        n = self._collection.count()
        if n == 0:
            return []
        result = self._collection.query(
            query_texts=[query],
            n_results=min(k, n),
            include=["documents", "metadatas", "distances"],
        )
        if not result or not result["ids"] or not result["ids"][0]:
            return []
        documents = result["documents"][0]
        metadatas = result["metadatas"][0] or []
        distances = result.get("distances")
        dist_list = (distances[0] if distances else None) or []
        out = []
        for i, doc in enumerate(documents):
            meta = metadatas[i] if i < len(metadatas) else {}
            out.append({
                "text": doc,
                "source_file": meta.get("source_file", ""),
                "chunk_index": meta.get("chunk_index", i),
                "start": meta.get("start", 0),
                "end": meta.get("end", 0),
                "distance": dist_list[i] if i < len(dist_list) else None,
            })
        return out

    def count(self) -> int:
        """Return total number of chunks in the store."""
        self._ensure_client()
        return self._collection.count()


def _chunk_id(source_file: str, chunk_index: int) -> str:
    """Stable id for a chunk (safe for Chroma)."""
    raw = f"{source_file}:{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

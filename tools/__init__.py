"""Tools invoked by agents: retrieval (RAG), memory read/write, policy checks.

All tool calls are logged (input, execution, result) for observability.

RAG retrieval:
- tools.retrieval.retrieval_tool(query, k=5) -> list[dict] with text, source_file, chunk_index, ...
- tools.vector_store.VectorStore for indexing and search
"""

from tools.retrieval import retrieval_tool, retrieve, get_vector_store

__all__ = ["retrieval_tool", "retrieve", "get_vector_store"]

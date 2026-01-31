# Task-003: RAG Pipeline (Indexing & Retrieval)

## Summary
Implement retrieval-augmented generation: index the knowledge corpus into a vector store and expose a retrieval tool that returns relevant context before any response generation.

## Scope
- Index all corpus documents (from Task-002) with the chosen chunking/overlap; no image indexing
- Clear separation: **retrieval** (search, return chunks) vs **reasoning** (consumed by agents later) vs **response synthesis** (separate agent)
- Retrieval tool: given a query, return top-k relevant chunks with references (e.g. source file, page/section)
- Responses in the system must reference retrieved context (enforced by agent design in Task-007)
- Store embeddings and metadata in a persistent store (e.g. vector DB or simple persistent index)

## Acceptance Criteria
- [ ] Corpus is indexed using defined chunk size and overlap
- [ ] Retrieval tool exists and is callable by agents; returns relevant context with source refs
- [ ] Retrieval happens before generation in the agent flow (no generation without retrieval step when KB is used)
- [ ] README or design doc states the retrieval → reasoning → synthesis separation

## Dependencies
- Task-001, Task-002

## Notes
- Implementation can live under `tools/` (e.g. retrieval tool) and a separate indexing script or module.

# Task-004: Memory System (Store, Persistence, Types)

## Summary
Implement a single memory store with type field (working / episodic / semantic), persistence across requests, session-scoped working memory with summarization for long threads, and read/write API for agents.

## Scope
- **Store:** One store (e.g. DB or structured files) with a `type` field: `working` | `episodic` | `semantic`
- **Working memory:** Per session/thread; short-lived; summarization (or windowing/pruning) when conversation is long to prevent unbounded growth
- **Episodic:** Past incidents, conversations, outcomes
- **Semantic:** Documents, FAQs, runbooks (can overlap with RAG or reference KB; keep consistent with problem statement)
- **Persistence:** Memory survives restarts and influences future decisions
- **API for agents:** Read and write from/to memory (used by Memory Agent and others in Task-007)
- **Memory UI:** CRUD-light: list memories, edit, delete (Task-009 will implement the UI; this task is backend/store + API)

## Acceptance Criteria
- [ ] Single store with type discrimination; agents can read and write
- [ ] Working memory is session-scoped and summarized (or pruned) for long chats
- [ ] Past interactions influence future decisions (demonstrable via episodic/semantic reads)
- [ ] Backend API or service layer for list/edit/delete so UI can consume it later

## Dependencies
- Task-001

## Notes
- Keep storage simple (e.g. SQLite + vector for semantic if needed, or one DB with type column). No images.

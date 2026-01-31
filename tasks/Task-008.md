# Task-008: Backend API (FastAPI & WebSocket Streaming)

## Summary
Expose the agent pipeline via FastAPI: chat/ticket endpoint and WebSocket for live streaming of agent events (high-level steps + expandable tool details). Support escalation marking and session/thread handling for long chats.

## Scope
- **REST/HTTP:** Endpoints as needed for health, config, and any non-streaming use (e.g. submit ticket/query, get session list)
- **Chat / ticket ingestion:** Accept incoming message or “ticket” (single-channel chat); normalize and pass to Ingestion Agent; run full graph
- **WebSocket:** Live stream of agent events: which agent ran, what data was used, tool calls (input, execution, result). Format suitable for UI to show high-level steps and expandable tool details
- **Session/thread:** Persist or associate messages with a session/thread ID for working memory and long-chat support (summarization from Task-004)
- **Escalation:** When Guardrails decide escalate, mark the conversation/ticket as “escalated” and include in API response or stream; store so UI can show “Escalated” state (no real ticket system)
- **Execute path:** Stub only (e.g. response field “recommended_actions” with a note that “execute” is not implemented)
- **Context management:** Backend respects working-memory summarization and bounded context for long chats (20+ turns)

## Acceptance Criteria
- [ ] FastAPI app runs; chat/ticket endpoint and WebSocket endpoint documented
- [ ] WebSocket streams agent events (agent name, step, tool calls with input/result)
- [ ] Escalation is marked and visible via API/stream; no external ticket integration
- [ ] Sessions/threads supported for multi-turn; long chats handled without unbounded context growth
- [ ] All config via env vars

## Dependencies
- Task-001, Task-007

## Notes
- UI will consume WebSocket in Task-009; ensure event schema is stable (e.g. JSON with type, agent_id, step, tool_calls, payload).

# Task-009: Frontend (React, Live Stream, Memory CRUD, Metrics)

## Summary
Build the React UI: chat interface, WebSocket-based live streaming of agent steps and tool calls, memory CRUD (list, edit, delete), basic metrics (latency, token usage, escalations), and responsive behavior for long chats.

## Scope
- **Chat UI:** Single-channel chat; user sends message, sees response; long chats (20+ turns) remain responsive (summarization handled by backend)
- **Live stream:** Connect via WebSocket; show high-level steps (which agent ran, when) and expandable tool call details (input, execution, result)
- **Explainability:** Display decision reason and evidence snippets (e.g. why escalated, which memory/knowledge was used); no chain-of-thought in UI
- **Memory UI:** List saved memories (working/episodic/semantic as needed); edit and delete; light CRUD
- **Metrics:** Basic metrics in UI: latency, token usage, escalation count (or rate); data from backend (Task-008 can expose metrics endpoint or include in stream)
- **Escalation:** Show “Escalated” state clearly when Guardrails escalate
- **Async updates:** When memory/observability writes complete asynchronously, UI can show late update (e.g. “Memory updated” or new event in stream)

## Acceptance Criteria
- [ ] React app with chat interface; WebSocket connection for live streaming
- [ ] Agent steps and expandable tool details visible in UI
- [ ] Memory list + edit + delete working against backend API
- [ ] Basic metrics (latency, tokens, escalations) visible in UI
- [ ] Long chats (20+ turns) do not degrade UI responsiveness; explainability (reason + evidence) shown where applicable
- [ ] All events from each agent live stream in UI as required by problem statement

## Dependencies
- Task-001 (UI skeleton), Task-004 (memory API for CRUD), Task-008 (WebSocket + API)

## Notes
- Use React state or a small store for stream buffer; optional “expand/collapse” per tool call for readability.

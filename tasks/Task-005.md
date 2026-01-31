# Task-005: Tools Layer & Observable Logging

## Summary
Implement the tools that agents will call (retrieval, memory read/write, policy/guardrails check) and ensure every tool’s input, execution, and result are logged so they can be streamed to the UI.

## Scope
- **Retrieval tool:** Wraps RAG retrieval (Task-003); same interface as needed by Knowledge Retrieval Agent
- **Memory tools:** Read from and write to memory (Task-004); used by Memory Agent and others
- **Policy / guardrails tool:** Call into guardrails layer (confidence, escalation rules); used by Guardrails Agent (Task-006)
- **Observable logging:** For each tool call: log input, start/end, and final result; structure so backend can stream “tool call” events to the UI (high-level step + expandable details)
- All tools in `tools/` (or under `tools/` submodules); no business logic inside agents beyond orchestration and delegation

## Acceptance Criteria
- [ ] Retrieval, memory (read/write), and policy/guardrails tools exist and are invokable
- [ ] Every tool logs: input, execution (e.g. start/end or duration), and result
- [ ] Log format supports streaming to UI (e.g. JSON events with tool name, args, result, timestamp)
- [ ] Clear separation: tools do the work; agents decide when to call them

## Dependencies
- Task-003 (retrieval), Task-004 (memory), Task-006 (guardrails) — or stub policy tool and implement in Task-006

## Notes
- Task-006 can implement the guardrails logic; Task-005 exposes it as a tool and ensures observability. If preferred, implement guardrails first (Task-006) then wire as tool here.

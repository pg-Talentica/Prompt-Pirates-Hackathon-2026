# Task-010: Testing & QA (Unit + Integration)

## Summary
Add unit tests per agent and 2–3 integration flows that exercise the full pipeline (e.g. happy path, escalation path, RAG + memory path). Ensure agentic behavior and tools are covered.

## Scope
- **Unit tests:** One or more tests per agent (or per agent file); mock tools/LLM where appropriate; verify delegation, tool invocation, or output shape
- **Integration tests:** 2–3 end-to-end flows, e.g.:
  - Happy path: user query → retrieval → reasoning → synthesized response (no escalation)
  - Escalation path: low confidence or policy trigger → Guardrails escalate → response marked escalated
  - RAG + memory path: query that triggers retrieval and episodic/semantic memory read; response references context
- **QA:** Tests run in CI or via single command (e.g. `pytest`); no flaky tests; use fixed or seeded data where possible
- **Dataset:** Tests may use a subset of the 100+ synthetic docs or dedicated test fixtures; avoid relying on live LLM for determinism where possible (or tag as integration and allow optional skip)

## Acceptance Criteria
- [ ] Unit tests exist for each agent (or per module); all pass
- [ ] At least 2–3 integration flows implemented and passing
- [ ] Single command to run full test suite (e.g. `pytest` or `npm test` for UI if applicable)
- [ ] README or CONTRIBUTING mentions how to run tests

## Dependencies
- Task-007 (agents and graph), Task-002/003 (data for integration), Task-006 (guardrails for escalation test)

## Notes
- Prefer pytest for Python; mock LLM calls in unit tests; integration tests can use a small model or allow env override for CI.

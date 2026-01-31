# Task-006: Guardrails & Safety (Dual Use + Escalation)

## Summary
Implement guardrails and safety so they are applied twice: right after ingestion (block unsafe input) and before final response (block unsafe output). Use a content-safety API plus configurable rules; support confidence thresholds and escalation (including “I don’t know” → no_answer/escalate).

## Scope
- **Content safety:** Integrate a content-safety API (e.g. OpenAI Moderation or similar) to detect violence, self-harm, sexual, hate, jailbreak; no hardcoded example strings—configurable rules or API-driven
- **First use — after ingestion:** Run guardrails on raw user input; block or escalate before any agent processing if unsafe
- **Second use — before final response:** Run guardrails on model/output before returning to user; block or replace with safe message if unsafe
- **Confidence thresholds:** Configurable; when confidence is low, route to escalation
- **Escalation policies:** Support policy-based escalation (e.g. intent-based or risk-based rules) in addition to low confidence
- **“I don’t know” path:** Structured no_answer or escalate path; Guardrails Agent interprets and decides escalate when appropriate
- **Ownership:** Guardrails owned by a dedicated Guardrails & Policy Agent (wired in Task-007)
- **Config:** All thresholds and rule references via env or config file, not hardcoded

## Acceptance Criteria
- [ ] Guardrails run after ingestion and before final response; both paths documented
- [ ] Content-safety API used; no hardcoded list of bad phrases
- [ ] Low-confidence and policy-based escalation supported; “I don’t know” handled via structured path
- [ ] Guardrails & Policy Agent is the single owner of these checks in the graph

## Dependencies
- Task-001

## Notes
- Expose guardrails as a callable layer so Task-005 can wrap it in a tool and Task-007 can invoke it from the Guardrails Agent.

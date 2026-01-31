# Task-007: LangGraph & All Agents (Orchestration & Execution Model)

## Summary
Implement the full agent graph in LangGraph: Ingestion → Planner/Orchestrator → parallel (Intent & Classification, Knowledge Retrieval, Memory) → Reasoning/Correlation → Response Synthesis → Guardrails & Policy → Final Response or Escalate. Each agent in a separate file/module; demonstrate serial, parallel, and async execution.

## Scope
- **Agents (each in its own file under `agents/`):**
  - Ingestion Agent: normalizes incoming ticket/query
  - Planner / Orchestrator Agent: decides execution strategy; chooses serial vs parallel vs async
  - Intent & Classification Agent: detects intent, urgency, SLA risk
  - Knowledge Retrieval Agent (RAG): calls retrieval tool; returns relevant context
  - Memory Agent: manages episodic and semantic memory (read/write via tools)
  - Reasoning / Correlation Agent: connects current issue with history; patterns and root causes; can write back to memory (dashed edge)
  - Response Synthesis Agent: generates human-readable output; feeds observability (dashed edge)
  - Guardrails & Policy Agent: applies safety (ingestion already guarded); decides auto-response vs escalate
- **Graph:** Match sample interaction diagram: Ingestion → Planner → parallel fan-out to Intent, Retrieval, Memory → Reasoning → Synthesis → Guardrails → Final Response | Escalate
- **Execution model:**
  - Serial: when dependencies exist (e.g. Ingestion → Planner → … → Guardrails)
  - Parallel: Intent, Knowledge Retrieval, and Memory agents run in parallel after Planner
  - Async: memory writes and observability events fire-and-forget; UI can show late updates
- **Single LLM** for all agents; tools (retrieval, memory, policy) called explicitly and observable
- **Execute path:** Stub only (e.g. “recommend” with a clear placeholder for “execute” later)
- **Escalation:** Mark as escalated and expose to API/UI; no real ticket integration

## Acceptance Criteria
- [ ] All eight agents implemented; each agent code in a different file/module under `agents/`
- [ ] LangGraph graph implements the specified flow with parallel branch (Intent + Retrieval + Memory)
- [ ] At least one example each: serial execution, parallel agent execution, async memory/observability writes
- [ ] No monolithic do-everything agent; clear delegation and tool usage
- [ ] Guardrails used twice: after ingestion (input) and before final response (output)
- [ ] Responses reference retrieved context; “I don’t know” flows to structured no_answer/escalate

## Dependencies
- Task-003 (RAG), Task-004 (memory), Task-005 (tools), Task-006 (guardrails)

## Notes
- Use LangGraph’s parallel node or map-reduce patterns for the fan-out. Async can be non-blocking publish or background task for memory/observability.

"""Shared state for the Support Co-Pilot agent graph.

Flows through: Ingestion → Planner → (Intent, Retrieval, Memory) → Reasoning
→ Synthesis → Guardrails → Final Response | Escalate.
"""

from __future__ import annotations

from typing import Any, TypedDict


class CoPilotState(TypedDict, total=False):
    """State passed between agents. All keys optional for partial updates."""

    # Input
    query: str
    session_id: str

    # After ingestion
    normalized_query: str
    input_guardrails_result: dict[str, Any]
    escalate: bool  # Early escalation after input guardrails

    # Parallel branch outputs (Intent, Retrieval, Memory)
    intent_result: dict[str, Any]
    retrieval_result: list[dict[str, Any]]
    memory_result: list[Any]

    # Reasoning
    reasoning_result: str

    # Synthesis
    draft_response: str

    # Guardrails (before final response)
    guardrails_result: dict[str, Any]

    # Output
    final_response: str
    recommended_actions: list[dict[str, Any]]  # Stub: execute path later

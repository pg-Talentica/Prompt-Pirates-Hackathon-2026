"""Ingestion Agent: normalizes incoming ticket/query and runs input guardrails.

Runs guardrails on raw user input (check_input). Harmful content: polite decline,
no escalation. Delegates to policy_tool(check_type="input").
"""

from __future__ import annotations

import logging
from typing import Any

from agents.state import CoPilotState
from tools.policy_tool import policy_check

logger = logging.getLogger(__name__)

# Polite decline when input is harmful/unsafe (no escalation)
HARMFUL_DECLINE_MESSAGE = (
    "I'm not able to assist with that request. I can only help with education loan "
    "queries—eligibility, policies, disbursement, or compliance. Please ask a related "
    "question or contact support for other inquiries."
)


def ingestion_agent(state: CoPilotState) -> dict[str, Any]:
    """Normalize query and run guardrails on input. Return partial state update."""
    query = (state.get("query") or "").strip() or ""
    # Normalize: strip, cap length, but preserve case for better retrieval matching
    # Lowercase is only used for guardrails check, not for retrieval
    normalized = query.strip()[:2000]
    normalized_lower = normalized.lower() if normalized else ""

    # Guardrails after ingestion: harmful content → polite decline, no escalation
    # Use lowercase for guardrails check
    result = policy_check(normalized_lower or normalized or query, check_type="input")
    safe = result.get("safe", True)

    # Harmful: set decline message; graph will route to decline (not escalate)
    escalate = False
    final_response = None
    if not safe:
        final_response = HARMFUL_DECLINE_MESSAGE
        logger.info("Ingestion: harmful input; returning polite decline (no escalation)")
    else:
        logger.info("Ingestion normalized query len=%d guardrails safe=%s", len(normalized or query), safe)

    out = {
        "normalized_query": normalized or query,
        "input_guardrails_result": result,
        "escalate": escalate,
    }
    if final_response is not None:
        out["final_response"] = final_response
    return out

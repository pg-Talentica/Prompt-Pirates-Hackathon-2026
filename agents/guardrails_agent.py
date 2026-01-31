"""Guardrails & Policy Agent: applies safety; decides auto-response vs escalate.

Runs guardrails on draft output (check_output). Second use of guardrails
(after ingestion). Owns the decision: Final Response | Escalate.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.state import CoPilotState
from tools.policy_tool import policy_check

logger = logging.getLogger(__name__)

SAFE_FALLBACK = "I'm unable to provide a response for this request. Please contact support or try rephrasing."


def guardrails_agent(state: CoPilotState) -> dict[str, Any]:
    """Run guardrails on draft response (before final response). Decide escalate or final_response."""
    if state.get("escalate"):
        # Already escalated at ingestion
        return {
            "guardrails_result": {"safe": False, "escalate": True, "reason": "input_guardrails"},
            "final_response": SAFE_FALLBACK,
        }
    draft = state.get("draft_response") or ""
    if not draft:
        return {"guardrails_result": {"escalate": True, "reason": "no_draft"}, "final_response": SAFE_FALLBACK}

    # Second use of guardrails: before final response
    result = policy_check(draft, check_type="output")
    safe = result.get("safe", True)
    escalate = result.get("escalate", False)
    no_answer = result.get("no_answer", False)

    if not safe:
        escalate = True
        final = SAFE_FALLBACK
    elif escalate and no_answer:
        final = "I don't have a confident answer for this. I've escalated your request to the team."
    elif escalate:
        final = "Your request has been escalated for further assistance."
    else:
        final = draft

    logger.info("Guardrails: safe=%s escalate=%s no_answer=%s", safe, escalate, no_answer)
    return {
        "guardrails_result": result,
        "escalate": escalate,
        "final_response": final,
    }

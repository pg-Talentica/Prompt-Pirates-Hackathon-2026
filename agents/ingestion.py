"""Ingestion Agent: normalizes incoming ticket/query and runs input guardrails.

Runs guardrails on raw user input (check_input) to block or escalate before
any agent processing if unsafe. Delegates to policy_tool(check_type="input").
"""

from __future__ import annotations

import logging
from typing import Any

from agents.state import CoPilotState
from tools.policy_tool import policy_check

logger = logging.getLogger(__name__)


def ingestion_agent(state: CoPilotState) -> dict[str, Any]:
    """Normalize query and run guardrails on input. Return partial state update."""
    query = (state.get("query") or "").strip() or ""
    normalized = query.strip().lower()[:2000]  # Normalize: strip, lower, cap length
    if not normalized and query:
        normalized = query.strip()[:2000]

    # Guardrails after ingestion (first use)
    result = policy_check(normalized or query, check_type="input")
    escalate = result.get("escalate", False) or not result.get("safe", True)

    logger.info("Ingestion normalized query len=%d guardrails safe=%s escalate=%s", len(normalized), result.get("safe"), escalate)
    return {
        "normalized_query": normalized or query,
        "input_guardrails_result": result,
        "escalate": escalate,
    }

"""Planner / Orchestrator Agent: decides execution strategy.

Chooses serial vs parallel vs async. For this graph we always run
Intent, Knowledge Retrieval, and Memory in parallel after this node.
Delegation only; no business logic.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.state import CoPilotState

logger = logging.getLogger(__name__)


def planner_agent(state: CoPilotState) -> dict[str, Any]:
    """Decide execution strategy. No state change; parallel branch follows."""
    if state.get("escalate"):
        logger.info("Planner: skip parallel branch (already escalated)")
        return {}
    logger.info("Planner: run Intent, Retrieval, Memory in parallel")
    return {}

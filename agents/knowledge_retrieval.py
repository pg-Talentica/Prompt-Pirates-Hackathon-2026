"""Knowledge Retrieval Agent (RAG): calls retrieval tool and returns relevant context.

Retrieval happens before generation; this agent only delegates to retrieval_tool.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.state import CoPilotState
from tools.retrieval import retrieval_tool

logger = logging.getLogger(__name__)


def knowledge_retrieval_agent(state: CoPilotState) -> dict[str, Any]:
    """Retrieve top-k chunks for the query. Return partial state update."""
    if state.get("escalate"):
        return {}
    query = state.get("normalized_query") or state.get("query") or ""
    if not query:
        return {"retrieval_result": []}

    results = retrieval_tool(query=query, k=5)
    logger.info("Retrieval returned %d chunks", len(results))
    return {"retrieval_result": results}

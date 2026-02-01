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

    # Try original query first
    results = retrieval_tool(query=query, k=8)
    logger.info("Retrieval returned %d chunks for query: %s", len(results), query[:100])
    
    # If no results, try query expansion for education loan queries
    if not results and any(keyword in query.lower() for keyword in ["loan", "policy", "eligibility", "student", "education", "abroad", "international"]):
        # Expand query with synonyms/related terms
        expanded_queries = [
            query,
            query + " education loan eligibility",
            query.replace("12th", "12th grade").replace("science", "science field"),
            "education loan policy " + query,
        ]
        for expanded in expanded_queries:
            if expanded != query:
                temp_results = retrieval_tool(query=expanded, k=8)
                if temp_results:
                    logger.info("Expanded query returned %d chunks: %s", len(temp_results), expanded[:100])
                    results = temp_results
                    break
    
    # Log retrieval details for debugging
    if results:
        distances = [r.get("distance") for r in results if r.get("distance") is not None]
        if distances:
            logger.info("Retrieval distances: min=%.4f, max=%.4f, avg=%.4f", 
                       min(distances), max(distances), sum(distances)/len(distances))
        sources = [r.get("source_file", "") for r in results[:3]]
        logger.info("Top sources: %s", ", ".join(sources))
    else:
        logger.warning("No retrieval results for query: %s", query[:100])
    
    return {"retrieval_result": results}

"""Reasoning / Correlation Agent: connects current issue with history; patterns and root causes.

Can write back to memory (dashed edge). Uses single LLM; consumes intent, retrieval, memory.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.state import CoPilotState
from tools.memory_tools import memory_write_tool

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "data/memory.db"


def _call_llm(prompt: str, system: str | None = None) -> str:
    try:
        from api.config import get_settings
        from openai import OpenAI
        settings = get_settings()
        if not settings.llm_api_key:
            return "Unable to correlate (no LLM configured)."
        client = OpenAI(api_key=settings.llm_api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=settings.model,
            messages=messages,
            max_tokens=500,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning("Reasoning LLM call failed: %s", e)
        return "Correlation unavailable (LLM error)."


def reasoning_agent(state: CoPilotState) -> dict[str, Any]:
    """Correlate intent, retrieval, memory; identify patterns and root causes. Return partial state update."""
    if state.get("escalate"):
        return {}
    query = state.get("normalized_query") or state.get("query") or ""
    intent = state.get("intent_result") or {}
    retrieval = state.get("retrieval_result") or []
    memory = state.get("memory_result") or {}

    # Build context from retrieval (reference retrieved context)
    retrieval_text = "\n\n".join(
        f"[{c.get('source_file', '')}]: {c.get('text', '')[:300]}..." for c in retrieval[:5]
    ) if retrieval else "No retrieved context."
    working = (memory.get("working") or [])[:10]
    working_text = "\n".join(f"{m.get('role', '')}: {m.get('content', '')[:100]}" for m in working) if working else "No working memory."

    system = "You are a support reasoning agent. Connect the current issue with history, identify patterns and root causes. Be concise."
    prompt = f"Query: {query}\nIntent: {intent}\n\nRetrieved context:\n{retrieval_text}\n\nWorking memory:\n{working_text}\n\nProvide reasoning and root cause analysis:"
    reasoning = _call_llm(prompt, system=system)

    # Async write to memory (fire-and-forget): store this reasoning as episodic
    try:
        memory_write_tool(
            type_="episodic",
            content=f"Query: {query}\nReasoning: {reasoning[:500]}",
            session_id=state.get("session_id"),
            metadata={"agent": "reasoning"},
        )
    except Exception as e:
        logger.debug("Async memory write skipped: %s", e)

    logger.info("Reasoning completed len=%d", len(reasoning))
    return {"reasoning_result": reasoning}

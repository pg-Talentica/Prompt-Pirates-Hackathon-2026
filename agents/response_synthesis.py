"""Response Synthesis Agent: generates human-readable output; feeds observability.

Must reference retrieved context. Execute path: stub only (recommend with placeholder).
"""

from __future__ import annotations

import logging
from typing import Any

from agents.state import CoPilotState
from datetime import datetime, timezone

from tools.observability import ToolCallEvent, emit_tool_event

logger = logging.getLogger(__name__)


def _call_llm(prompt: str, system: str | None = None) -> str:
    try:
        from api.config import get_settings
        from openai import OpenAI
        settings = get_settings()
        if not settings.llm_api_key:
            return "I don't have enough context to answer. Please provide more details or contact support."
        client = OpenAI(api_key=settings.llm_api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=settings.model,
            messages=messages,
            max_tokens=800,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning("Synthesis LLM call failed: %s", e)
        return "I'm unable to generate a response right now. Please try again or escalate to support."


def response_synthesis_agent(state: CoPilotState) -> dict[str, Any]:
    """Generate human-readable response from reasoning and retrieved context. Return partial state update."""
    if state.get("escalate"):
        return {}
    query = state.get("normalized_query") or state.get("query") or ""
    reasoning = state.get("reasoning_result") or ""
    retrieval = state.get("retrieval_result") or []
    intent = state.get("intent_result") or {}

    # Reference retrieved context (mandatory)
    refs = [c.get("source_file", "") for c in retrieval[:5] if c.get("source_file")]
    retrieval_summary = "Based on: " + ", ".join(refs) if refs else "No sources."
    context_block = "\n\n".join(
        f"From {c.get('source_file', '')}:\n{c.get('text', '')[:400]}"
        for c in retrieval[:3]
    ) if retrieval else "No retrieved context."

    system = "You are a support agent. Give a clear, human-readable answer. Always reference the retrieved sources. If you don't know, say 'I don't know' clearly. Do not make up information."
    prompt = f"Query: {query}\nIntent: {intent}\n\nReasoning:\n{reasoning}\n\nRetrieved context:\n{context_block}\n\nProvide a helpful response that references the above. End with: [Sources: {retrieval_summary}]"
    draft = _call_llm(prompt, system=system)

    # Stub: recommended actions (execute path later)
    recommended_actions = [
        {"action": "recommend", "description": "Review and recommend next steps", "execute_stub": True},
    ]

    # Observability (dashed edge): emit synthesis event
    try:
        emit_tool_event(ToolCallEvent(
            tool_name="response_synthesis",
            input={"query_len": len(query), "retrieval_count": len(retrieval)},
            started_at=datetime.now(timezone.utc).isoformat(),
            finished_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=0,
            result={"draft_len": len(draft), "sources": refs},
            error=None,
        ))
    except Exception:
        pass

    logger.info("Synthesis draft len=%d", len(draft))
    return {
        "draft_response": draft,
        "recommended_actions": recommended_actions,
    }

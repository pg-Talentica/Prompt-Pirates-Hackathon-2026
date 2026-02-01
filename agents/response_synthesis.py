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
        from tools.langfuse_observability import get_openai_client
        settings = get_settings()
        if not settings.llm_api_key:
            return "I don't have enough context to answer. Please provide more details or contact support."
        client = get_openai_client()
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


OUT_OF_CONTEXT_MESSAGE = (
    "I don't have information about that in my knowledge base. "
    "My expertise is limited to education loans and fintech (Kredila, HDFC, SBI, ICICI): "
    "loan policies, eligibility, disbursement runbooks, troubleshooting delays, incident reports, "
    "and regulatory compliance (RBI). Please ask a question related to these topics, or contact support."
)


def response_synthesis_agent(state: CoPilotState) -> dict[str, Any]:
    """Generate human-readable response from reasoning and retrieved context. Return partial state update."""
    if state.get("escalate"):
        return {}
    query = state.get("normalized_query") or state.get("query") or ""
    reasoning = state.get("reasoning_result") or ""
    retrieval = state.get("retrieval_result") or []
    intent = state.get("intent_result") or {}

    # No relevant context: do not call LLM; respond that it's outside our scope
    if not retrieval:
        logger.info("No retrieval context for query; returning out-of-context response")
        return {
            "draft_response": OUT_OF_CONTEXT_MESSAGE,
            "recommended_actions": [{"description": "Ask about education loans, eligibility, or disbursement."}],
        }

    # Stricter relevance gate: best result must be within confidence threshold
    distances = [c.get("distance") for c in retrieval if c.get("distance") is not None]
    if distances:
        try:
            from api.config import get_settings
            conf_threshold = get_settings().rag_confidence_max_distance
        except Exception:
            conf_threshold = 1.1
        best_distance = min(distances)
        if best_distance > conf_threshold:
            logger.info("Best retrieval distance %.3f > %.2f; returning out-of-context", best_distance, conf_threshold)
            return {
                "draft_response": OUT_OF_CONTEXT_MESSAGE,
                "recommended_actions": [{"description": "Try rephrasing your question about loans or eligibility."}],
            }

    # Reference retrieved context (mandatory)
    refs = [c.get("source_file", "") for c in retrieval[:5] if c.get("source_file")]
    retrieval_summary = "Based on: " + ", ".join(refs) if refs else "No sources."
    context_block = "\n\n".join(
        f"From {c.get('source_file', '')}:\n{c.get('text', '')[:400]}"
        for c in retrieval[:3]
    )

    system = (
        "You are a customer support agent for Kredila education loans. "
        "Answer ONLY using the retrieved context below. "
        "If the query is not related to the context, respond: 'I don't have information about that in my knowledge base. Please ask about Kredila education loans, eligibility, runbooks, or compliance.' "
        "Never make up information. Never answer questions outside the provided context. "
        "Always cite the source documents."
    )
    prompt = f"Query: {query}\nIntent: {intent}\n\nReasoning:\n{reasoning}\n\nRetrieved context:\n{context_block}\n\nProvide a helpful response based ONLY on the above context. End with: [Sources: {retrieval_summary}]"
    draft = _call_llm(prompt, system=system)

    # Stub: recommended actions (execute path later)
    recommended_actions = [
        {"description": "Ask a follow-up question if you need more details."},
        {"description": "Contact support if you need personalized assistance."},
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

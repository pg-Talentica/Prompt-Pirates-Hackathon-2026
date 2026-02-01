"""Intent & Classification Agent: detects intent, urgency, SLA risk.

Uses single LLM (from config). Delegates to tool usage; no monolithic logic.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from agents.state import CoPilotState

logger = logging.getLogger(__name__)


def _call_llm(prompt: str, system: str | None = None) -> str:
    try:
        from api.config import get_settings
        from tools.langfuse_observability import get_openai_client
        settings = get_settings()
        if not settings.llm_api_key:
            return '{"intent": "unknown", "urgency": "medium", "sla_risk": "low"}'
        client = get_openai_client()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=settings.model,
            messages=messages,
            max_tokens=200,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text
    except Exception as e:
        logger.warning("Intent LLM call failed: %s", e)
        return '{"intent": "unknown", "urgency": "medium", "sla_risk": "low"}'


def intent_agent(state: CoPilotState) -> dict[str, Any]:
    """Classify intent, urgency, SLA risk. Return partial state update."""
    if state.get("escalate"):
        return {}
    query = state.get("normalized_query") or state.get("query") or ""
    if not query:
        return {"intent_result": {"intent": "unknown", "urgency": "medium", "sla_risk": "low"}}

    system = (
        "You are a support classifier for education loan queries. Respond with ONLY a JSON object "
        "with keys: intent (string), urgency (low|medium|high), sla_risk (low|medium|high), "
        "requires_human_escalation (boolean). "
        "Set requires_human_escalation=true when: (1) query is about a loan/application/disbursement "
        "AND (2) user explicitly asks to speak to an agent/human/support OR (3) user has an urgent "
        "blocking issue (stuck, delayed, failed, error) that likely needs human intervention. "
        "Set false for general info questions (policies, eligibility, rates) even if urgent."
    )
    prompt = f"Classify this support query:\n{query[:500]}"
    raw = _call_llm(prompt, system=system)
    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        obj = json.loads(raw)
        req_human = obj.get("requires_human_escalation")
        if isinstance(req_human, bool):
            pass
        elif isinstance(req_human, str):
            req_human = req_human.lower() in ("true", "yes", "1")
        else:
            req_human = False
        result = {
            "intent": str(obj.get("intent", "unknown")),
            "urgency": str(obj.get("urgency", "medium")),
            "sla_risk": str(obj.get("sla_risk", "low")),
            "requires_human_escalation": bool(req_human),
        }
    except Exception:
        result = {"intent": "unknown", "urgency": "medium", "sla_risk": "low", "requires_human_escalation": False}
    logger.info("Intent result: %s", result)
    return {"intent_result": result}

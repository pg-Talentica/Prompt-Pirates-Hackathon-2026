"""Guardrails & Policy Agent: applies safety; decides polite decline vs escalate.

- Harmful content: polite decline, NO escalation.
- Escalate ONLY when query is loan-related, urgent, and requires human intervention.
- Otherwise: polite decline (can't do / don't have knowledge).
- Uses intent_result (urgency, sla_risk) + query keywords for reliable classification.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from agents.state import CoPilotState
from tools.policy_tool import policy_check

logger = logging.getLogger(__name__)

# Polite decline when we can't help (no escalation)
POLITE_DECLINE = (
    "I'm not able to help with that. My expertise is limited to education loans "
    "(eligibility, policies, disbursement, compliance). Please ask a related question "
    "or contact support for other inquiries."
)

# Polite decline for harmful output
HARMFUL_DECLINE = (
    "I'm not able to provide a response for that request. Please ask about education "
    "loans, eligibility, disbursement, or contact support."
)

# Escalate message (only when loan+urgent+human)
ESCALATE_MESSAGE = "Your request has been escalated for further assistance. Our team will reach out shortly."

# Loan-related: education loan, disbursement, application, etc.
_LOAN_PATTERNS = (
    r"\bloan\b", r"\bdisbursement\b", r"\bdisbursed\b", r"\bdisbursing\b",
    r"\bapplication\b", r"\bapply\b", r"\bsanction\b", r"\beligibility\b",
    r"\bemi\b", r"\brepayment\b", r"\bsanctioned\b", r"\bapproval\b",
    r"\bapprove\b", r"\bfunding\b", r"\bdisburse\b",
)
# Urgency/distress signals
_URGENCY_PATTERNS = (
    r"\burgent\b", r"\bemergency\b", r"\basap\b", r"\bimmediately\b",
    r"\bstuck\b", r"\bdelay\b", r"\bdelayed\b", r"\bnot working\b",
    r"\bfailed\b", r"\berror\b", r"\bissue\b", r"\bproblem\b",
    r"\bnot getting\b", r"\bhaven't received\b", r"\bhasn't been\b",
    r"\bwaiting\b", r"\bblocked\b", r"\bneed\b", r"\brequire\b",
)
# Explicit request for human/support
_HUMAN_PATTERNS = (
    r"\bspeak to\b", r"\btalk to\b", r"\bagent\b", r"\bhuman\b",
    r"\bescalate\b", r"\bhelp\b", r"\bassist\b", r"\bcontact\b",
    r"\brepresentative\b", r"\bsupport\b", r"\bsomeone\b", r"\bofficer\b",
    r"\bcall back\b", r"\bcallback\b", r"\breach out\b",
)


def _query_requires_escalation(query: str, intent_result: dict[str, Any] | None) -> bool:
    """Classify if query should be escalated: loan-related AND (urgent OR human requested).

    Uses: (1) keyword matching on query, (2) intent_result (urgency, sla_risk, requires_human_escalation).
    Returns True only when all criteria are met for safe, consistent escalation.
    """
    q = (query or "").lower()
    intent = intent_result or {}
    urgency = str(intent.get("urgency", "medium")).lower()
    sla_risk = str(intent.get("sla_risk", "low")).lower()
    llm_requires_escalation = intent.get("requires_human_escalation") is True

    has_loan = any(re.search(p, q) for p in _LOAN_PATTERNS)
    has_urgency = any(re.search(p, q) for p in _URGENCY_PATTERNS)
    has_human = any(re.search(p, q) for p in _HUMAN_PATTERNS)
    intent_high_urgency = urgency == "high"
    intent_high_risk = sla_risk in ("high", "medium")

    # LLM explicitly classified as requiring human escalation (and loan-related)
    if llm_requires_escalation and has_loan:
        return True

    # Must be loan-related for keyword-based path
    if not has_loan:
        return False

    # Loan + (explicit human request OR urgency in query OR high intent urgency+risk)
    if has_human:
        return True
    if has_urgency:
        return True
    if intent_high_urgency and intent_high_risk:
        return True
    return False


def guardrails_agent(state: CoPilotState) -> dict[str, Any]:
    """Run guardrails on draft response. Harmful → polite decline. Escalate only when loan+urgent+human."""
    if state.get("escalate"):
        return {
            "guardrails_result": {"safe": False, "escalate": False, "reason": "input_guardrails"},
            "final_response": POLITE_DECLINE,
            "escalate": False,
            "recommended_actions": [{"description": "Contact support for further assistance."}],
        }
    query = state.get("normalized_query") or state.get("query") or ""
    intent_result = state.get("intent_result") or {}
    draft = state.get("draft_response") or ""

    # Explicit escalation: user clearly requests human (loan + urgent/human)
    if _query_requires_escalation(query, intent_result):
        logger.info("Guardrails: query requires escalation (loan+urgent+human); escalating")
        return {
            "guardrails_result": {"escalate": True, "reason": "explicit_escalation_request"},
            "final_response": ESCALATE_MESSAGE,
            "escalate": True,
            "recommended_actions": [{"description": "A support agent will reach out to you shortly."}],
        }

    if not draft:
        return {
            "guardrails_result": {"escalate": False, "reason": "no_draft"},
            "final_response": POLITE_DECLINE,
            "escalate": False,
            "recommended_actions": [{"description": "Contact support for further assistance."}],
        }

    result = policy_check(draft, check_type="output")
    safe = result.get("safe", True)
    no_answer = result.get("no_answer", False)
    confidence = result.get("confidence", 1.0)

    # Harmful output: polite decline, NO escalation
    if not safe:
        logger.info("Guardrails: harmful output; polite decline (no escalation)")
        return {
            "guardrails_result": result,
            "escalate": False,
            "final_response": HARMFUL_DECLINE,
            "recommended_actions": [{"description": "Contact support for further assistance."}],
        }

    # No answer or low confidence: escalate ONLY if loan+urgent+human (already checked above;
    # if we reach here, query did not require escalation, so polite decline)
    try:
        from api.config import get_settings
        conf_threshold = get_settings().guardrails_confidence_threshold
    except Exception:
        conf_threshold = 0.7
    if no_answer or confidence < conf_threshold:
        # Double-check: sometimes draft triggers no_answer but query actually needs escalation
        if _query_requires_escalation(query, intent_result):
            logger.info("Guardrails: no_answer/low_confidence + loan+urgent+human; escalating")
            return {
                "guardrails_result": result,
                "escalate": True,
                "final_response": ESCALATE_MESSAGE,
                "recommended_actions": [{"description": "A support agent will reach out to you shortly."}],
            }
        logger.info("Guardrails: no_answer/low_confidence; polite decline")
        return {
            "guardrails_result": result,
            "escalate": False,
            "final_response": draft,
            "recommended_actions": [{"description": "Ask a follow-up question or contact support."}],
        }

    return {"guardrails_result": result, "escalate": False, "final_response": draft}

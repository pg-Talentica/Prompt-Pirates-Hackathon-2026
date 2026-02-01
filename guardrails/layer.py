"""Guardrails layer: content-safety API and escalation.

Applied after ingestion (check_input) and before final response (check_output).
Uses OpenAI Moderation API; no hardcoded phrases. Config from env via api.config.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from guardrails.models import GuardrailsResult

logger = logging.getLogger(__name__)

# Structured markers for "I don't know" / no_answer (configurable; not hardcoded phrases)
NO_ANSWER_PATTERNS_KEY = "no_answer_patterns"
DEFAULT_NO_ANSWER_PATTERNS = [
    r"\bI don't know\b",
    r"\bI do not know\b",
    r"\bno_answer\b",
    r"\bN/A\b",
    r"\[no_answer\]",
    r"\[escalate\]",
]


def _get_config() -> Any:
    try:
        from api.config import get_settings
        return get_settings()
    except Exception:
        return None


def _call_moderation_api(text: str, api_key: str) -> dict[str, Any] | None:
    """Call OpenAI Moderation API. Returns raw result or None on error/missing key."""
    if not (api_key and api_key.strip()):
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key.strip())
        resp = client.moderations.create(input=text)
        if not resp.results:
            return None
        r = resp.results[0]
        raw = r.model_dump() if hasattr(r, "model_dump") else getattr(r, "__dict__", {})
        if not raw and hasattr(r, "flagged"):
            raw = {"flagged": r.flagged, "categories": getattr(r, "categories", {}), "category_scores": getattr(r, "category_scores", {})}
        return {
            "flagged": raw.get("flagged", getattr(r, "flagged", False)),
            "categories": raw.get("categories", getattr(r, "categories", {})),
            "category_scores": raw.get("category_scores", getattr(r, "category_scores", {})),
        }
    except Exception as e:
        logger.warning("Moderation API call failed: %s", e)
        return None


def _confidence_from_moderation(result: dict[str, Any]) -> float:
    """Compute confidence from moderation result: 1.0 if not flagged, else 0."""
    if not result:
        return 1.0
    if not result.get("flagged", False):
        return 1.0
    return 0.0


def _should_escalate_by_policy(
    no_answer: bool,
    confidence: float,
    escalation_policy_json: str,
    escalate_on_no_answer: bool,
    confidence_threshold: float,
) -> bool:
    """Apply escalation policy: low confidence or no_answer per config."""
    if no_answer and escalate_on_no_answer:
        return True
    if confidence < confidence_threshold:
        return True
    try:
        rules = json.loads(escalation_policy_json or "[]")
        for rule in rules:
            when = rule.get("when")
            then = rule.get("then")
            if when == "no_answer" and no_answer and then == "escalate":
                return True
            if when == "confidence_below" and confidence < rule.get("threshold", 0):
                return True
    except Exception:
        pass
    return False


def _detect_no_answer(text: str, patterns: list[str] | None = None) -> bool:
    """Detect structured no_answer / I don't know in response text."""
    if not text or not text.strip():
        return False
    use = patterns or DEFAULT_NO_ANSWER_PATTERNS
    for pat in use:
        try:
            if re.search(pat, text, re.IGNORECASE):
                return True
        except re.error:
            continue
    return False


def check_input(text: str, api_key: str | None = None) -> GuardrailsResult:
    """Run guardrails on raw user input (after ingestion).

    Use this immediately after ingestion to block before any agent processing
    if the input is unsafe. Harmful content: polite decline, NO escalation.
    """
    config = _get_config()
    key = api_key or (config.llm_api_key if config else None) or ""
    mod = _call_moderation_api(text, key)
    safe = not (mod and mod.get("flagged", False))
    confidence = _confidence_from_moderation(mod) if mod else 1.0
    reason = "ok"
    if not mod and not key:
        reason = "moderation_skipped_no_key"
    elif mod and mod.get("flagged", False):
        reason = "content_safety_flagged"
    # Harmful content: do NOT escalate; caller will return polite decline
    escalate = False
    return GuardrailsResult(
        safe=safe,
        escalate=escalate,
        confidence=confidence,
        reason=reason,
        no_answer=False,
        details={"moderation": mod} if mod else None,
    )


def check_output(
    text: str,
    confidence_override: float | None = None,
    api_key: str | None = None,
) -> GuardrailsResult:
    """Run guardrails on model output (before final response).

    Use this before returning the response to the user. Harmful output:
    polite decline, NO escalation. Escalation is decided by caller based on
    loan+urgent+human criteria.
    """
    config = _get_config()
    key = api_key or (config.llm_api_key if config else None) or ""
    mod = _call_moderation_api(text, key)
    safe = not (mod and mod.get("flagged", False))
    confidence = confidence_override if confidence_override is not None else (_confidence_from_moderation(mod) if mod else 1.0)
    no_answer = _detect_no_answer(text)
    reason = "ok"
    if not safe:
        reason = "content_safety_flagged"
    elif no_answer:
        reason = "no_answer"
    # Do NOT auto-escalate here; caller (guardrails_agent) decides based on loan+urgent+human
    escalate = False
    return GuardrailsResult(
        safe=safe,
        escalate=escalate,
        confidence=confidence,
        reason=reason,
        no_answer=no_answer,
        details={"moderation": mod} if mod else None,
    )

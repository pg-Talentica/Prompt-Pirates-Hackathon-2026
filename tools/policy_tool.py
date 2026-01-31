"""Policy / guardrails tool for agents (Guardrails Agent).

Calls the guardrails layer (Task-006): content-safety API, confidence thresholds,
escalation policies, and structured no_answer path. Applied after ingestion
(input) and before final response (output).
"""

from __future__ import annotations

from typing import Any

from guardrails.layer import check_input, check_output
from tools.observability import wrap_tool


def policy_check(
    input_text: str,
    check_type: str = "input",
    confidence_override: float | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Run policy/guardrails check on text.

    - check_type='input': run after ingestion (raw user input). Use to block
      or escalate before any agent processing if unsafe.
    - check_type='output': run before final response (model output). Use to
      block or replace with safe message; supports no_answer (I don't know)
      and escalation policy.

    Returns dict with: safe, escalate, confidence, reason, no_answer, details.
    Used by Guardrails Agent (Task-007).
    """
    if check_type == "output":
        result = check_output(input_text, confidence_override=confidence_override, api_key=api_key)
    else:
        result = check_input(input_text, api_key=api_key)
    return result.to_dict()


policy_tool = wrap_tool("policy_check", policy_check)

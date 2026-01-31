"""Guardrails & safety: content-safety API, confidence thresholds, escalation.

Applied twice: after ingestion (block unsafe input) and before final response
(block unsafe output). No hardcoded phrases; config via env.
"""

from guardrails.layer import check_input, check_output
from guardrails.models import GuardrailsResult

__all__ = ["GuardrailsResult", "check_input", "check_output"]

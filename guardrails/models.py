"""Guardrails result and config models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class GuardrailsResult:
    """Result of a guardrails check (input or output)."""

    safe: bool
    escalate: bool
    confidence: float
    reason: str
    no_answer: bool = False
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "safe": self.safe,
            "escalate": self.escalate,
            "confidence": self.confidence,
            "reason": self.reason,
            "no_answer": self.no_answer,
            "details": self.details,
        }

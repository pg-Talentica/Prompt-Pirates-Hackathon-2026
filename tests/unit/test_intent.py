"""Unit tests for Intent Agent."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.intent import intent_agent
from agents.state import CoPilotState


@patch("agents.intent._call_llm")
def test_intent_returns_classification(mock_llm: object, sample_state: CoPilotState) -> None:
    """Intent agent returns intent_result with intent, urgency, sla_risk."""
    mock_llm.return_value = '{"intent": "howto", "urgency": "medium", "sla_risk": "low"}'
    out = intent_agent(sample_state)
    assert "intent_result" in out
    assert out["intent_result"]["intent"] == "howto"
    assert out["intent_result"]["urgency"] == "medium"
    assert out["intent_result"]["sla_risk"] == "low"
    mock_llm.assert_called_once()


@patch("agents.intent._call_llm")
def test_intent_skips_when_escalated(mock_llm: object, sample_state_escalated: CoPilotState) -> None:
    """Intent agent returns empty when state is already escalated."""
    out = intent_agent(sample_state_escalated)
    assert out == {}
    mock_llm.assert_not_called()


@patch("agents.intent._call_llm")
def test_intent_fallback_on_invalid_json(mock_llm: object, sample_state: CoPilotState) -> None:
    """Intent agent returns fallback when LLM returns non-JSON."""
    mock_llm.return_value = "not json"
    out = intent_agent(sample_state)
    assert "intent_result" in out
    assert out["intent_result"]["intent"] == "unknown"
    assert out["intent_result"]["urgency"] == "medium"
    assert out["intent_result"]["sla_risk"] == "low"

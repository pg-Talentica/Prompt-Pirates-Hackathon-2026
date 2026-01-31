"""Unit tests for Ingestion Agent."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.ingestion import ingestion_agent
from agents.state import CoPilotState


@patch("agents.ingestion.policy_check")
def test_ingestion_normalizes_query_and_returns_state(mock_policy: object, sample_state: CoPilotState) -> None:
    """Ingestion normalizes query and returns normalized_query, input_guardrails_result, escalate."""
    mock_policy.return_value = {"safe": True, "escalate": False, "reason": "ok"}
    out = ingestion_agent(sample_state)
    assert "normalized_query" in out
    assert out["normalized_query"].strip().lower() == sample_state["query"].strip().lower()[:2000]
    assert "input_guardrails_result" in out
    assert out["input_guardrails_result"] == {"safe": True, "escalate": False, "reason": "ok"}
    assert out["escalate"] is False
    mock_policy.assert_called_once()


@patch("agents.ingestion.policy_check")
def test_ingestion_escalate_when_policy_unsafe(mock_policy: object, sample_state: CoPilotState) -> None:
    """When policy_check returns escalate=True, state has escalate=True."""
    mock_policy.return_value = {"safe": False, "escalate": True}
    out = ingestion_agent(sample_state)
    assert out["escalate"] is True
    assert out["input_guardrails_result"]["escalate"] is True


@patch("agents.ingestion.policy_check")
def test_ingestion_empty_query(mock_policy: object) -> None:
    """Empty query still returns state with normalized_query and guardrails result."""
    mock_policy.return_value = {"safe": True, "escalate": False}
    out = ingestion_agent({"query": "  ", "session_id": "x"})
    assert "normalized_query" in out
    assert "input_guardrails_result" in out
    assert "escalate" in out

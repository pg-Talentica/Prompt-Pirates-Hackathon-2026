"""Unit tests for Guardrails Agent."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.guardrails_agent import guardrails_agent
from agents.state import CoPilotState


@patch("agents.guardrails_agent.policy_check")
def test_guardrails_passes_draft_when_safe(
    mock_policy: object,
    sample_state_with_reasoning: CoPilotState,
) -> None:
    """When policy_check returns safe and not escalate, final_response is the draft."""
    sample_state_with_reasoning["draft_response"] = "Helpful answer here."
    sample_state_with_reasoning["recommended_actions"] = []
    mock_policy.return_value = {"safe": True, "escalate": False, "no_answer": False}
    out = guardrails_agent(sample_state_with_reasoning)
    assert out["final_response"] == "Helpful answer here."
    assert out["escalate"] is False
    assert "guardrails_result" in out


@patch("agents.guardrails_agent.policy_check")
def test_guardrails_escalates_when_policy_escalate(
    mock_policy: object,
    sample_state_with_reasoning: CoPilotState,
) -> None:
    """When policy_check returns escalate, final_response is escalation message."""
    sample_state_with_reasoning["draft_response"] = "Draft."
    sample_state_with_reasoning["recommended_actions"] = []
    mock_policy.return_value = {"safe": True, "escalate": True, "no_answer": False}
    out = guardrails_agent(sample_state_with_reasoning)
    assert out["escalate"] is True
    assert "escalated" in out["final_response"].lower() or "assistance" in out["final_response"].lower()


@patch("agents.guardrails_agent.policy_check")
def test_guardrails_already_escalated_at_ingestion(
    mock_policy: object,
    sample_state_escalated: CoPilotState,
) -> None:
    """When state already has escalate=True, returns guardrails_result and safe fallback."""
    out = guardrails_agent(sample_state_escalated)
    assert out["escalate"] is True
    assert "final_response" in out
    assert out["guardrails_result"]["reason"] == "input_guardrails"
    mock_policy.assert_not_called()


@patch("agents.guardrails_agent.policy_check")
def test_guardrails_no_draft_escalates(
    mock_policy: object,
    sample_state: CoPilotState,
) -> None:
    """When draft_response is empty, guardrails escalate with reason no_draft."""
    sample_state["escalate"] = False
    sample_state["draft_response"] = ""
    out = guardrails_agent(sample_state)
    assert out["escalate"] is True
    assert out["guardrails_result"]["reason"] == "no_draft"
    mock_policy.assert_not_called()

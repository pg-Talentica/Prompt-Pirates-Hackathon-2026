"""Unit tests for Guardrails Agent."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.guardrails_agent import _query_requires_escalation, guardrails_agent
from agents.state import CoPilotState


def test_query_requires_escalation_loan_urgent_human() -> None:
    """Query with loan + urgency + human request → escalate."""
    assert _query_requires_escalation("My loan is stuck, I need to speak to an agent", None) is True
    assert _query_requires_escalation("Loan disbursement delayed 15 days, contact support", None) is True
    assert _query_requires_escalation("Urgent: disbursement not working, help!", None) is True


def test_query_requires_escalation_loan_only_no_escalate() -> None:
    """Query with loan only (no urgency/human) → no escalate."""
    assert _query_requires_escalation("What are the loan policies?", None) is False
    assert _query_requires_escalation("Tell me about eligibility", None) is False


def test_query_requires_escalation_with_intent() -> None:
    """Intent requires_human_escalation + loan → escalate."""
    intent = {"urgency": "high", "sla_risk": "high", "requires_human_escalation": True}
    assert _query_requires_escalation("My loan application status", intent) is True


def test_query_requires_escalation_non_loan_no_escalate() -> None:
    """Non-loan query → never escalate."""
    assert _query_requires_escalation("Who is Raghu?", None) is False
    assert _query_requires_escalation("I need help with API rate limit", None) is False


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
def test_guardrails_escalates_when_query_requires_escalation(
    mock_policy: object,
    sample_state_with_reasoning: CoPilotState,
) -> None:
    """When query is loan+urgent+human, final_response is escalation message."""
    sample_state_with_reasoning["query"] = "My loan disbursement is stuck, I need to speak to an agent"
    sample_state_with_reasoning["normalized_query"] = "my loan disbursement is stuck, i need to speak to an agent"
    sample_state_with_reasoning["intent_result"] = {"urgency": "high", "sla_risk": "high", "requires_human_escalation": True}
    sample_state_with_reasoning["draft_response"] = "Draft."
    sample_state_with_reasoning["recommended_actions"] = []
    mock_policy.return_value = {"safe": True, "escalate": False, "no_answer": False}
    out = guardrails_agent(sample_state_with_reasoning)
    assert out["escalate"] is True
    assert "escalated" in out["final_response"].lower() or "assistance" in out["final_response"].lower()


@patch("agents.guardrails_agent.policy_check")
def test_guardrails_already_escalated_at_ingestion(
    mock_policy: object,
    sample_state_escalated: CoPilotState,
) -> None:
    """When state already has escalate=True (harmful input path), returns polite decline, no escalation."""
    out = guardrails_agent(sample_state_escalated)
    assert out["escalate"] is False  # Harmful input: polite decline, do NOT escalate
    assert "final_response" in out
    assert out["guardrails_result"]["reason"] == "input_guardrails"
    mock_policy.assert_not_called()


@patch("agents.guardrails_agent.policy_check")
def test_guardrails_no_draft_polite_decline(
    mock_policy: object,
    sample_state: CoPilotState,
) -> None:
    """When draft_response is empty and query does not require escalation, polite decline."""
    sample_state["escalate"] = False
    sample_state["draft_response"] = ""
    out = guardrails_agent(sample_state)
    assert out["escalate"] is False  # No draft alone does not escalate; query must require human
    assert out["guardrails_result"]["reason"] == "no_draft"
    mock_policy.assert_not_called()

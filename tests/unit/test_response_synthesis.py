"""Unit tests for Response Synthesis Agent."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.response_synthesis import response_synthesis_agent
from agents.state import CoPilotState


@patch("agents.response_synthesis._call_llm")
def test_synthesis_returns_draft_and_recommended_actions(
    mock_llm: object,
    sample_state_with_reasoning: CoPilotState,
) -> None:
    """Response synthesis returns draft_response and recommended_actions."""
    mock_llm.return_value = "You can reset the rate limit from the admin panel. [Sources: runbook_003.txt]"
    out = response_synthesis_agent(sample_state_with_reasoning)
    assert "draft_response" in out
    assert "recommended_actions" in out
    assert "admin panel" in out["draft_response"]
    assert isinstance(out["recommended_actions"], list)
    assert len(out["recommended_actions"]) >= 1
    mock_llm.assert_called_once()


@patch("agents.response_synthesis._call_llm")
def test_synthesis_skips_when_escalated(
    mock_llm: object,
    sample_state_escalated: CoPilotState,
) -> None:
    """Response synthesis returns empty when escalated."""
    out = response_synthesis_agent(sample_state_escalated)
    assert out == {}
    mock_llm.assert_not_called()

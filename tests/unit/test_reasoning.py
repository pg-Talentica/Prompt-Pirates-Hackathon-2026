"""Unit tests for Reasoning Agent."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.reasoning import reasoning_agent
from agents.state import CoPilotState


@patch("agents.reasoning.memory_write_tool")
@patch("agents.reasoning._call_llm")
def test_reasoning_returns_reasoning_result(
    mock_llm: object,
    mock_memory_write: object,
    sample_state_with_parallel_outputs: CoPilotState,
) -> None:
    """Reasoning agent returns reasoning_result from LLM."""
    mock_llm.return_value = "Root cause: configuration issue. Recommend checking admin panel."
    out = reasoning_agent(sample_state_with_parallel_outputs)
    assert "reasoning_result" in out
    assert "Root cause" in out["reasoning_result"]
    mock_llm.assert_called_once()
    mock_memory_write.assert_called_once()


@patch("agents.reasoning._call_llm")
def test_reasoning_skips_when_escalated(
    mock_llm: object,
    sample_state_escalated: CoPilotState,
) -> None:
    """Reasoning agent returns empty when escalated."""
    out = reasoning_agent(sample_state_escalated)
    assert out == {}
    mock_llm.assert_not_called()

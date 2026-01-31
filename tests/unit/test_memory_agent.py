"""Unit tests for Memory Agent."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agents.memory_agent import memory_agent
from agents.state import CoPilotState


@patch("agents.memory_agent.memory_read_tool")
def test_memory_agent_returns_working_episodic_semantic(
    mock_memory_read: object,
    sample_state: CoPilotState,
    temp_memory_db: Path,
) -> None:
    """Memory agent returns memory_result with working, episodic, semantic."""
    mock_memory_read.side_effect = [[], []]  # episodic, semantic (each call returns [])
    with patch("agents.memory_agent.DEFAULT_DB_PATH", str(temp_memory_db)):
        out = memory_agent(sample_state)
    assert "memory_result" in out
    assert "working" in out["memory_result"]
    assert "episodic" in out["memory_result"]
    assert "semantic" in out["memory_result"]
    assert out["memory_result"]["episodic"] == []
    assert out["memory_result"]["semantic"] == []
    assert mock_memory_read.call_count == 2


def test_memory_agent_skips_when_escalated(
    sample_state_escalated: CoPilotState,
    temp_memory_db: Path,
) -> None:
    """Memory agent returns empty when escalated."""
    with patch("agents.memory_agent.DEFAULT_DB_PATH", str(temp_memory_db)):
        out = memory_agent(sample_state_escalated)
    assert out == {}

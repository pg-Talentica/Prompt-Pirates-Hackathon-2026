"""Unit tests for Planner Agent."""

from __future__ import annotations

import pytest

from agents.planner import planner_agent
from agents.state import CoPilotState


def test_planner_returns_empty_when_not_escalated(sample_state: CoPilotState) -> None:
    """Planner returns empty update when state is not escalated."""
    out = planner_agent(sample_state)
    assert out == {}


def test_planner_returns_empty_when_escalated(sample_state_escalated: CoPilotState) -> None:
    """Planner returns empty update when already escalated (no state change)."""
    out = planner_agent(sample_state_escalated)
    assert out == {}

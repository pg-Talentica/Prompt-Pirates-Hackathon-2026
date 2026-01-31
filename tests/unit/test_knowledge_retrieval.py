"""Unit tests for Knowledge Retrieval Agent."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.knowledge_retrieval import knowledge_retrieval_agent
from agents.state import CoPilotState


@patch("agents.knowledge_retrieval.retrieval_tool")
def test_retrieval_returns_results(mock_retrieval: object, sample_state: CoPilotState) -> None:
    """Knowledge retrieval agent returns retrieval_result from tool."""
    mock_retrieval.return_value = [
        {"text": "chunk1", "source_file": "a.txt", "chunk_index": 0},
    ]
    out = knowledge_retrieval_agent(sample_state)
    assert "retrieval_result" in out
    assert len(out["retrieval_result"]) == 1
    assert out["retrieval_result"][0]["source_file"] == "a.txt"
    mock_retrieval.assert_called_once_with(query=sample_state["query"], k=5)


@patch("agents.knowledge_retrieval.retrieval_tool")
def test_retrieval_skips_when_escalated(mock_retrieval: object, sample_state_escalated: CoPilotState) -> None:
    """Knowledge retrieval returns empty when escalated."""
    out = knowledge_retrieval_agent(sample_state_escalated)
    assert out == {}
    mock_retrieval.assert_not_called()


@patch("agents.knowledge_retrieval.retrieval_tool")
def test_retrieval_empty_query_returns_empty_list(mock_retrieval: object) -> None:
    """When query is empty, returns retrieval_result [] without calling tool."""
    out = knowledge_retrieval_agent({"query": "", "session_id": "x", "escalate": False})
    assert out["retrieval_result"] == []
    mock_retrieval.assert_not_called()

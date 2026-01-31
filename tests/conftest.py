"""Pytest fixtures for Support Co-Pilot tests.

Shared fixtures: sample state, mocks for LLM/tools, temp memory DB.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agents.state import CoPilotState


@pytest.fixture
def sample_state() -> CoPilotState:
    """Minimal state for agent tests."""
    return {
        "query": "How do I reset the API rate limit?",
        "session_id": "test-session",
    }


@pytest.fixture
def sample_state_escalated() -> CoPilotState:
    """State with escalate=True (early exit path)."""
    return {
        "query": "test",
        "session_id": "test-session",
        "normalized_query": "test",
        "input_guardrails_result": {"safe": False, "escalate": True},
        "escalate": True,
    }


@pytest.fixture
def sample_state_with_parallel_outputs() -> CoPilotState:
    """State after parallel branch (intent, retrieval, memory)."""
    return {
        "query": "How do I reset the API rate limit?",
        "session_id": "test-session",
        "normalized_query": "how do i reset the api rate limit?",
        "escalate": False,
        "intent_result": {"intent": "howto", "urgency": "medium", "sla_risk": "low"},
        "retrieval_result": [
            {
                "text": "To reset the API rate limit, use the admin panel.",
                "source_file": "runbook_003.txt",
                "chunk_index": 0,
                "start": 0,
                "end": 100,
            }
        ],
        "memory_result": {
            "working": [{"role": "user", "content": "Previous question"}],
            "episodic": [],
            "semantic": [],
        },
    }


@pytest.fixture
def sample_state_with_reasoning(sample_state_with_parallel_outputs: CoPilotState) -> CoPilotState:
    """State after reasoning (for synthesis and guardrails)."""
    base: CoPilotState = dict(sample_state_with_parallel_outputs)
    base["reasoning_result"] = "User needs to reset rate limit; runbook suggests admin panel."
    return base


@pytest.fixture
def temp_memory_db(tmp_path: Path) -> Path:
    """Temporary SQLite path for memory tests (no :memory: to avoid mkdir)."""
    return tmp_path / "memory.db"


def mock_policy_check_safe(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Guardrails check returning safe, no escalation."""
    return {
        "safe": True,
        "escalate": False,
        "confidence": 0.9,
        "reason": "ok",
        "no_answer": False,
        "details": {},
    }


def mock_policy_check_escalate(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Guardrails check returning escalate."""
    return {
        "safe": False,
        "escalate": True,
        "confidence": 0.3,
        "reason": "policy",
        "no_answer": False,
        "details": {},
    }


def mock_retrieval_tool(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    """Retrieval tool returning fixed chunks."""
    return [
        {
            "text": "To reset the API rate limit, open the admin panel and click Reset.",
            "source_file": "runbook_003.txt",
            "chunk_index": 0,
            "start": 0,
            "end": 200,
        }
    ]


def mock_memory_read_tool(*args: Any, **kwargs: Any) -> list[Any]:
    """Memory read tool returning empty or minimal list."""
    return []


def mock_call_llm_intent(*args: Any, **kwargs: Any) -> str:
    """LLM response for intent agent (JSON)."""
    return '{"intent": "howto", "urgency": "medium", "sla_risk": "low"}'


def mock_call_llm_reasoning(*args: Any, **kwargs: Any) -> str:
    """LLM response for reasoning agent."""
    return "The user needs to reset the API rate limit. The runbook indicates using the admin panel."


def mock_call_llm_synthesis(*args: Any, **kwargs: Any) -> str:
    """LLM response for response synthesis agent."""
    return "You can reset the API rate limit from the admin panel. [Sources: runbook_003.txt]"

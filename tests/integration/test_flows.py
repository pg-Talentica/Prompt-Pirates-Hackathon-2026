"""Integration tests: full pipeline flows (happy path, escalation, RAG + memory).

Mocks LLM and tools at boundaries so tests run without live API or vector store.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents import get_graph
from agents.state import CoPilotState


def _mock_policy_safe(*args: object, **kwargs: object) -> dict:
    return {"safe": True, "escalate": False, "confidence": 0.9, "reason": "ok", "no_answer": False, "details": {}}


def _mock_policy_escalate(*args: object, **kwargs: object) -> dict:
    return {"safe": False, "escalate": True, "confidence": 0.2, "reason": "policy", "no_answer": False, "details": {}}


def _mock_retrieval(*args: object, **kwargs: object) -> list:
    return [
        {
            "text": "To reset the API rate limit, use the admin panel under Settings.",
            "source_file": "runbook_003.txt",
            "chunk_index": 0,
            "start": 0,
            "end": 200,
        }
    ]


def _mock_memory_read(*args: object, **kwargs: object) -> list:
    return []


def _mock_llm_intent(*args: object, **kwargs: object) -> str:
    return '{"intent": "howto", "urgency": "medium", "sla_risk": "low"}'


def _mock_llm_reasoning(*args: object, **kwargs: object) -> str:
    return "User needs to reset rate limit. Runbook indicates using the admin panel."


def _mock_llm_synthesis(*args: object, **kwargs: object) -> str:
    return "You can reset the API rate limit from the admin panel. [Sources: runbook_003.txt]"


@pytest.mark.integration
@patch("agents.response_synthesis._call_llm", side_effect=_mock_llm_synthesis)
@patch("agents.reasoning._call_llm", side_effect=_mock_llm_reasoning)
@patch("agents.intent._call_llm", side_effect=_mock_llm_intent)
@patch("agents.memory_agent.memory_read_tool", side_effect=_mock_memory_read)
@patch("agents.knowledge_retrieval.retrieval_tool", side_effect=_mock_retrieval)
@patch("agents.ingestion.policy_check", side_effect=_mock_policy_safe)
@patch("agents.guardrails_agent.policy_check", side_effect=_mock_policy_safe)
def test_happy_path(
    mock_guardrails: object,
    mock_ingestion_policy: object,
    mock_retrieval: object,
    mock_memory_read: object,
    mock_intent_llm: object,
    mock_reasoning_llm: object,
    mock_synthesis_llm: object,
    temp_memory_db: object,
) -> None:
    """Happy path: user query → retrieval → reasoning → synthesized response (no escalation)."""
    with patch("agents.memory_agent.DEFAULT_DB_PATH", str(temp_memory_db)), patch(
        "memory.store.DEFAULT_DB_PATH", temp_memory_db
    ):
        graph = get_graph()
        state = graph.invoke(
            {"query": "How do I reset the API rate limit?", "session_id": "integration-test"},
            config={"configurable": {"thread_id": "integration-test"}},
        )
    assert state.get("escalate") is False
    assert state.get("final_response")
    assert "admin panel" in state["final_response"].lower() or "rate limit" in state["final_response"].lower()
    assert state.get("intent_result")
    assert state.get("retrieval_result")
    assert state.get("reasoning_result")
    assert state.get("draft_response")
    mock_retrieval.assert_called()
    mock_guardrails.assert_called()


@pytest.mark.integration
@patch("agents.ingestion.policy_check", side_effect=_mock_policy_escalate)
def test_escalation_path(
    mock_policy: object,
) -> None:
    """Escalation path: input guardrails trigger escalate → response marked escalated."""
    graph = get_graph()
    state = graph.invoke(
        {"query": "Sensitive or unsafe input", "session_id": "integration-escalate"},
        config={"configurable": {"thread_id": "integration-escalate"}},
    )
    assert state.get("escalate") is True
    assert state.get("final_response")
    assert "escalat" in state["final_response"].lower() or "assistance" in state["final_response"].lower()
    mock_policy.assert_called_once()


@pytest.mark.integration
@patch("agents.response_synthesis._call_llm", side_effect=_mock_llm_synthesis)
@patch("agents.reasoning._call_llm", side_effect=_mock_llm_reasoning)
@patch("agents.intent._call_llm", side_effect=_mock_llm_intent)
@patch("agents.memory_agent.memory_read_tool", side_effect=_mock_memory_read)
@patch("agents.knowledge_retrieval.retrieval_tool", side_effect=_mock_retrieval)
@patch("agents.ingestion.policy_check", side_effect=_mock_policy_safe)
@patch("agents.guardrails_agent.policy_check", side_effect=_mock_policy_safe)
def test_rag_memory_path(
    mock_guardrails: object,
    mock_ingestion_policy: object,
    mock_retrieval: object,
    mock_memory_read: object,
    mock_intent_llm: object,
    mock_reasoning_llm: object,
    mock_synthesis_llm: object,
    temp_memory_db: object,
) -> None:
    """RAG + memory path: query triggers retrieval and memory read; response references context."""
    with patch("agents.memory_agent.DEFAULT_DB_PATH", str(temp_memory_db)), patch(
        "memory.store.DEFAULT_DB_PATH", temp_memory_db
    ):
        graph = get_graph()
        state = graph.invoke(
            {"query": "Where is the rate limit reset documented?", "session_id": "integration-rag"},
            config={"configurable": {"thread_id": "integration-rag"}},
        )
    assert state.get("escalate") is False
    assert state.get("final_response")
    assert state.get("retrieval_result")
    assert len(state["retrieval_result"]) >= 1
    assert state["retrieval_result"][0].get("source_file") == "runbook_003.txt"
    assert state.get("memory_result") is not None
    mock_retrieval.assert_called()
    mock_memory_read.assert_called()

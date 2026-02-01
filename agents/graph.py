"""LangGraph definition: Ingestion → Planner → parallel (Intent, Retrieval, Memory)
→ Reasoning → Synthesis → Guardrails → Final Response | Escalate.

Serial: ingestion → planner → … → guardrails.
Parallel: Intent, Knowledge Retrieval, Memory run in parallel after Planner.
Async: memory writes and observability in reasoning/synthesis are fire-and-forget.
"""

from __future__ import annotations

from typing import Literal

from agents.state import CoPilotState
from agents.ingestion import ingestion_agent
from agents.planner import planner_agent
from agents.intent import intent_agent
from agents.knowledge_retrieval import knowledge_retrieval_agent
from agents.memory_agent import memory_agent
from agents.reasoning import reasoning_agent
from agents.response_synthesis import response_synthesis_agent
from agents.guardrails_agent import guardrails_agent
from tools.langfuse_observability import trace_agent

try:
    from langgraph.graph import StateGraph, START, END
except ImportError:
    try:
        from langgraph.graph import StateGraph
        START = "__start__"
        END = "__end__"
    except ImportError:
        START = "__start__"
        END = "__end__"
        StateGraph = None  # type: ignore


def _route_after_ingestion(state: CoPilotState) -> Literal["planner", "escalate", "decline"]:
    """Harmful input → decline (polite message); else continue to planner."""
    if state.get("final_response") and not state.get("input_guardrails_result", {}).get("safe", True):
        return "decline"
    if state.get("escalate"):
        return "escalate"
    return "planner"


def _route_after_guardrails(state: CoPilotState) -> Literal["response", "escalate"]:
    """Route to final response or escalate based on guardrails result."""
    if state.get("escalate"):
        return "escalate"
    return "response"


def _terminal_response(state: CoPilotState) -> dict:
    """Passthrough terminal node (Final Response)."""
    return {}


def _terminal_escalate(state: CoPilotState) -> dict:
    """Terminal node (Escalate). Ensure final_response set when skipped from ingestion."""
    if state.get("final_response"):
        return {}
    return {"final_response": "Your request has been escalated for further assistance."}


def _terminal_decline(state: CoPilotState) -> dict:
    """Terminal node (Decline). Polite decline message, no escalation."""
    return {}


def build_graph():
    """Build and compile the Support Co-Pilot graph."""
    if StateGraph is None:
        raise ImportError("Install langgraph: pip install langgraph")

    builder = StateGraph(CoPilotState)

    # Nodes (each agent instrumented for Langfuse observability)
    builder.add_node("ingestion", trace_agent(ingestion_agent, "ingestion"))
    builder.add_node("planner", trace_agent(planner_agent, "planner"))
    builder.add_node("intent", trace_agent(intent_agent, "intent"))
    builder.add_node("retrieval", trace_agent(knowledge_retrieval_agent, "retrieval"))
    builder.add_node("memory", trace_agent(memory_agent, "memory"))
    builder.add_node("reasoning", trace_agent(reasoning_agent, "reasoning"))
    builder.add_node("synthesis", trace_agent(response_synthesis_agent, "synthesis"))
    builder.add_node("guardrails", trace_agent(guardrails_agent, "guardrails"))
    builder.add_node("response", _terminal_response)
    builder.add_node("escalate", _terminal_escalate)
    builder.add_node("decline", _terminal_decline)

    # Serial: START → ingestion; then conditional (decline | escalate | planner)
    builder.add_edge(START, "ingestion")
    builder.add_conditional_edges(
        "ingestion",
        _route_after_ingestion,
        path_map={"planner": "planner", "escalate": "escalate", "decline": "decline"},
    )

    # Parallel: planner → intent, retrieval, memory (all three run)
    builder.add_edge("planner", "intent")
    builder.add_edge("planner", "retrieval")
    builder.add_edge("planner", "memory")

    # Fan-in: reasoning runs once after intent, retrieval, memory all complete
    builder.add_edge(["intent", "retrieval", "memory"], "reasoning")

    # Serial: reasoning → synthesis → guardrails
    builder.add_edge("reasoning", "synthesis")
    builder.add_edge("synthesis", "guardrails")

    # Conditional: guardrails → response | escalate
    builder.add_conditional_edges(
        "guardrails",
        _route_after_guardrails,
        path_map={"response": "response", "escalate": "escalate"},
    )
    builder.add_edge("response", END)
    builder.add_edge("escalate", END)
    builder.add_edge("decline", END)

    return builder.compile()


# Compiled graph singleton for API use
_graph = None


def get_graph():
    """Return compiled graph (lazy)."""
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph

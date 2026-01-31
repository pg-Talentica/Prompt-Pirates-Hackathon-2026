"""Stable WebSocket event schema for agent pipeline streaming.

Events are JSON objects with type, optional agent_id/step, tool_calls, and payload.
Consumed by UI (Task-009) for high-level steps and expandable tool details.
"""

from __future__ import annotations

from typing import Any, Literal

# Event types sent over WebSocket
StreamEventType = Literal[
    "agent_step",   # An agent (node) completed; payload = state update
    "tool_call",    # A tool was invoked; payload = ToolCallEvent-like dict
    "escalation",   # Guardrails decided to escalate
    "done",         # Pipeline finished; payload = final response summary
    "error",        # Pipeline or connection error
]


def agent_step_event(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Build agent_step event: which agent ran and state update."""
    return {
        "type": "agent_step",
        "agent_id": agent_id,
        "step": agent_id,
        "payload": _sanitize_payload(payload),
    }


def tool_call_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Build tool_call event: tool name, input, result, timestamps."""
    return {
        "type": "tool_call",
        "tool_calls": [payload],
        "payload": payload,
    }


def escalation_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Build escalation event: conversation/ticket marked as escalated."""
    return {
        "type": "escalation",
        "payload": _sanitize_payload(payload),
    }


def done_event(
    final_response: str,
    escalate: bool,
    recommended_actions: list[dict[str, Any]],
    intent_result: dict[str, Any] | None = None,
    guardrails_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build done event: final response or escalation summary."""
    return {
        "type": "done",
        "payload": _sanitize_payload({
            "final_response": final_response,
            "escalate": escalate,
            "recommended_actions": recommended_actions,
            "intent_result": intent_result,
            "guardrails_result": guardrails_result,
        }),
    }


def error_event(message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build error event."""
    return {
        "type": "error",
        "payload": {"message": message, **(details or {})},
    }


def _sanitize_payload(obj: Any, max_str: int = 2000, max_list: int = 50) -> Any:
    """Make payload JSON-serializable and bounded for streaming."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        if isinstance(obj, str) and len(obj) > max_str:
            return obj[:max_str] + "..."
        return obj
    if isinstance(obj, (list, tuple)):
        seq = list(obj)
        if len(seq) > max_list:
            return [_sanitize_payload(v, max_str, max_list) for v in seq[:max_list]] + [f"... {len(seq) - max_list} more"]
        return [_sanitize_payload(v, max_str, max_list) for v in seq]
    if isinstance(obj, dict):
        return {k: _sanitize_payload(v, max_str, max_list) for k, v in list(obj.items())[:50]}
    try:
        return str(obj)[:500]
    except Exception:
        return "<unserializable>"

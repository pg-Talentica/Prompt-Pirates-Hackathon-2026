"""Observable logging for tool calls: input, execution, result.

Structured events (tool_name, args, result, timestamps) for streaming to the UI.
Backend (Task-008) can register callbacks to push events to WebSocket.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Callbacks registered for streaming (e.g. push to WebSocket per request)
_tool_event_callbacks: list[Callable[[dict[str, Any]], None]] = []


@dataclass
class ToolCallEvent:
    """Structured event for a single tool call (streamable to UI)."""

    tool_name: str
    input: dict[str, Any]
    started_at: str
    finished_at: str
    duration_ms: float
    result: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict for streaming."""
        d = asdict(self)
        d["result"] = _safe_value(d.get("result"))
        return d


def emit_tool_event(event: ToolCallEvent) -> None:
    """Log and broadcast the tool call event to registered callbacks."""
    payload = event.to_dict()
    logger.info(
        "tool_call tool_name=%s duration_ms=%.2f error=%s",
        event.tool_name,
        event.duration_ms,
        event.error,
        extra={"tool_event": payload},
    )
    for cb in _tool_event_callbacks:
        try:
            cb(payload)
        except Exception as e:
            logger.warning("Tool event callback failed: %s", e)


def register_tool_event_callback(callback: Callable[[dict[str, Any]], None]) -> None:
    """Register a callback to receive tool call events (e.g. for WebSocket streaming)."""
    _tool_event_callbacks.append(callback)


def unregister_tool_event_callback(callback: Callable[[dict[str, Any]], None]) -> None:
    """Remove a previously registered callback."""
    if callback in _tool_event_callbacks:
        _tool_event_callbacks.remove(callback)


def wrap_tool(tool_name: str, fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a tool so that each call logs input, execution, and result and emits a ToolCallEvent."""

    def observed(*args: Any, **kwargs: Any) -> Any:
        started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()
        input_payload: dict[str, Any] = {}
        # Build input from fn signature or positional/kwargs
        try:
            if kwargs:
                input_payload = dict(kwargs)
            if args:
                # For positional args, use arg0, arg1 or param names if inspectable
                for i, a in enumerate(args):
                    input_payload[f"arg_{i}"] = _safe_value(a)
        except Exception:
            input_payload = {"args": str(args), "kwargs": str(kwargs)}

        result: Any = None
        error: str | None = None
        try:
            result = fn(*args, **kwargs)
            return result
        except Exception as e:
            error = str(e)
            raise
        finally:
            t1 = time.perf_counter()
            finished_at = datetime.now(timezone.utc).isoformat()
            duration_ms = (t1 - t0) * 1000
            event = ToolCallEvent(
                tool_name=tool_name,
                input=input_payload,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=round(duration_ms, 2),
                result=_safe_value(result),
                error=error,
            )
            emit_tool_event(event)

    observed.__name__ = fn.__name__
    observed.__doc__ = fn.__doc__
    return observed


def _safe_value(x: Any) -> Any:
    """Return a JSON-serializable value for logging (truncate long strings/lists)."""
    if x is None:
        return None
    if isinstance(x, (str, int, float, bool)):
        if isinstance(x, str) and len(x) > 2000:
            return x[:2000] + "..."
        return x
    if isinstance(x, (list, tuple)):
        seq = list(x)
        if len(seq) > 50:
            return [_safe_value(v) for v in seq[:50]] + [f"... {len(seq) - 50} more"]
        return [_safe_value(v) for v in seq]
    if isinstance(x, dict):
        return {k: _safe_value(v) for k, v in list(x.items())[:50]}
    try:
        return str(x)[:500]
    except Exception:
        return "<unserializable>"

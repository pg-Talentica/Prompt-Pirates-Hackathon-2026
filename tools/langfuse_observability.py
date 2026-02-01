"""Langfuse observability: traces, spans, token usage, model, duration per agent.

When LANGFUSE_SECRET_KEY is set, all agent runs are traced to Langfuse.
Each agent appears as a span with input/output, duration; LLM calls capture
input_tokens, output_tokens, model, and cost.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Generator

logger = logging.getLogger(__name__)


def _langfuse_enabled() -> bool:
    """Return True if Langfuse credentials are configured."""
    try:
        from api.config import get_settings
        s = get_settings()
        return bool(s.langfuse_secret_key and s.langfuse_secret_key.strip())
    except Exception:
        return False


def get_openai_client():
    """Return OpenAI client. If Langfuse enabled, returns Langfuse-wrapped client for auto-tracing."""
    try:
        from api.config import get_settings
        settings = get_settings()
    except Exception:
        settings = None
    if not settings or not settings.llm_api_key:
        from openai import OpenAI
        return OpenAI(api_key="")  # Will fail on first call
    if _langfuse_enabled():
        try:
            from langfuse.openai import OpenAI as LangfuseOpenAI
            return LangfuseOpenAI(api_key=settings.llm_api_key)
        except ImportError:
            from openai import OpenAI
            return OpenAI(api_key=settings.llm_api_key)
    from openai import OpenAI
    return OpenAI(api_key=settings.llm_api_key)


def trace_agent(agent_fn: Callable[[dict], dict], agent_name: str) -> Callable[[dict], dict]:
    """Wrap an agent to create a Langfuse span with input/output, duration, metadata."""

    def wrapped(state: dict) -> dict:
        if not _langfuse_enabled():
            return agent_fn(state)
        try:
            from langfuse import get_client
            langfuse = get_client()
            t0 = time.perf_counter()
            with langfuse.start_as_current_observation(
                as_type="span",
                name=agent_name,
                input={"query": state.get("query", "")[:500], "session_id": state.get("session_id", "")},
                metadata={"agent": agent_name},
            ) as span:
                result = agent_fn(state)
                duration_ms = (time.perf_counter() - t0) * 1000
                span.update(
                    output={k: (str(v)[:500] if isinstance(v, str) else v) for k, v in list(result.items())[:5]},
                    metadata={"duration_ms": round(duration_ms, 2), "agent": agent_name},
                )
                return result
        except Exception as e:
            logger.warning("Langfuse span for %s failed: %s", agent_name, e)
            return agent_fn(state)

    wrapped.__name__ = agent_fn.__name__
    return wrapped


@contextmanager
def trace_request(query: str, session_id: str) -> Generator[Any, None, None]:
    """Context manager for top-level request trace. Yields trace context for nested spans."""
    if not _langfuse_enabled():
        yield None
        return
    try:
        from langfuse import get_client
        langfuse = get_client()
        with langfuse.start_as_current_observation(
            as_type="trace",
            name="copilot-request",
            input={"query": query[:1000], "session_id": session_id},
            metadata={"session_id": session_id},
        ) as trace:
            yield trace
    except Exception as e:
        logger.warning("Langfuse trace failed: %s", e)
        yield None


def update_trace_outcome(trace_ctx: Any, state: dict) -> None:
    """Update Langfuse trace with outcome: escalated vs final_response. Call before exiting trace_request."""
    if trace_ctx is None:
        return
    try:
        escalated = bool(state.get("escalate", False))
        outcome = "escalated" if escalated else "final_response"
        final_response = state.get("final_response") or ""
        trace_ctx.update_trace(
            output={
                "outcome": outcome,
                "escalated": escalated,
                "final_response_preview": final_response[:300],
            },
            name=f"copilot-request → {outcome}",
            tags=[outcome],
            metadata={"session_id": state.get("session_id", ""), "outcome": outcome},
        )
    except Exception as e:
        logger.debug("Failed to update trace outcome: %s", e)


def flush_langfuse() -> None:
    """Flush Langfuse client (call before process exit in short-lived workers)."""
    if not _langfuse_enabled():
        return
    try:
        from langfuse import get_client
        get_client().flush()
    except Exception as e:
        logger.debug("Langfuse flush: %s", e)

"""Chat/ticket endpoint and WebSocket streaming for agent pipeline.

- POST /api/chat: sync invoke, returns final response or escalation.
- WebSocket /api/chat/ws: live stream of agent_step, tool_call, escalation, done.
Session/thread supported via session_id; escalation marked in response and stream.
"""

from __future__ import annotations

import asyncio
import logging
from queue import Queue
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from api.schemas.stream import (
    agent_step_event,
    done_event,
    error_event,
    escalation_event,
    tool_call_event,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    """Request body for chat/ticket."""

    query: str = Field(..., min_length=1, description="User message or ticket text")
    session_id: str = Field(default="default", description="Session/thread id for working memory")


class ChatResponse(BaseModel):
    """Response: final response or escalation. recommended_actions is stub (execute not implemented)."""

    final_response: str
    escalate: bool
    recommended_actions: list = Field(default_factory=list)
    intent_result: Optional[dict] = None
    guardrails_result: Optional[dict] = None


# --- REST: POST /api/chat ---


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Run the agent graph on the query and return final response or escalation.
    For live agent steps and tool calls, use WebSocket /api/chat/ws."""
    try:
        from agents import get_graph
        from tools.langfuse_observability import trace_request, update_trace_outcome

        graph = get_graph()
        with trace_request(req.query.strip(), req.session_id) as trace_ctx:
            state = graph.invoke(
                {"query": req.query.strip(), "session_id": req.session_id},
                config={"configurable": {"thread_id": req.session_id}},
            )
            update_trace_outcome(trace_ctx, state)
        return ChatResponse(
            final_response=state.get("final_response", ""),
            escalate=state.get("escalate", False),
            recommended_actions=state.get("recommended_actions", []),
            intent_result=state.get("intent_result"),
            guardrails_result=state.get("guardrails_result"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- WebSocket: /api/chat/ws ---


def _run_graph_stream(
    query: str,
    session_id: str,
    queue: Queue[tuple[str, Any]],
) -> None:
    """Run graph.stream in this thread; put stream chunks and tool events into queue."""
    from tools.observability import register_tool_event_callback, unregister_tool_event_callback

    def on_tool_event(ev: dict[str, Any]) -> None:
        queue.put(("tool_call", ev))

    register_tool_event_callback(on_tool_event)
    last_state: Optional[dict] = None
    try:
        from agents import get_graph
        from tools.langfuse_observability import trace_request

        graph = get_graph()
        config = {"configurable": {"thread_id": session_id}}
        inputs = {"query": query.strip(), "session_id": session_id}
        with trace_request(query.strip(), session_id) as trace_ctx:
            stream_mode = ["updates", "values"]
            try:
                stream_iter = graph.stream(inputs, stream_mode=stream_mode, config=config)
            except TypeError:
                stream_iter = graph.stream(inputs, stream_mode="updates", config=config)
                stream_mode = ["updates"]
            for event in stream_iter:
                if isinstance(event, (list, tuple)) and len(event) == 2:
                    mode, chunk = event[0], event[1]
                else:
                    mode, chunk = "updates", event
                if mode == "values":
                    last_state = chunk if isinstance(chunk, dict) else last_state
                queue.put(("stream", mode, chunk))
            if last_state is not None:
                from tools.langfuse_observability import update_trace_outcome
                update_trace_outcome(trace_ctx, last_state)
    except Exception as e:
        logger.exception("Graph stream error: %s", e)
        queue.put(("error", str(e)))
    finally:
        unregister_tool_event_callback(on_tool_event)
        queue.put(("done", last_state))


@router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    """Live stream of agent events: agent_step, tool_call, escalation, done.
    Client sends JSON: { \"query\": \"...\", \"session_id\": \"...\" } (session_id optional).
    Server sends JSON events: type agent_step | tool_call | escalation | done | error."""
    await websocket.accept()
    try:
        data = await websocket.receive_json()
    except Exception as e:
        await websocket.send_json(error_event("Invalid JSON or missing query", {"detail": str(e)}))
        await websocket.close()
        return
    query = data.get("query") or data.get("message", "")
    session_id = data.get("session_id", "default")
    if not query or not str(query).strip():
        await websocket.send_json(error_event("Missing or empty query"))
        await websocket.close()
        return
    query = str(query).strip()
    session_id = str(session_id).strip() or "default"

    queue: Queue[tuple[str, Any]] = Queue()
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        _run_graph_stream,
        query,
        session_id,
        queue,
    )

    try:
        while True:
            item = await loop.run_in_executor(None, queue.get)
            kind = item[0]
            if kind == "done":
                last_state = item[1] or {}
                escalate = last_state.get("escalate", False)
                if escalate:
                    await websocket.send_json(escalation_event({
                        "final_response": last_state.get("final_response", ""),
                        "guardrails_result": last_state.get("guardrails_result"),
                    }))
                await websocket.send_json(done_event(
                    final_response=last_state.get("final_response", ""),
                    escalate=escalate,
                    recommended_actions=last_state.get("recommended_actions", []),
                    intent_result=last_state.get("intent_result"),
                    guardrails_result=last_state.get("guardrails_result"),
                ))
                break
            if kind == "error":
                await websocket.send_json(error_event(item[1]))
                break
            if kind == "stream":
                _, mode, chunk = item
                if mode == "updates" and isinstance(chunk, dict):
                    for node_name, update in chunk.items():
                        await websocket.send_json(agent_step_event(node_name, update))
            if kind == "tool_call":
                await websocket.send_json(tool_call_event(item[1]))
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.exception("WebSocket error: %s", e)
        try:
            await websocket.send_json(error_event(str(e)))
        except Exception:
            pass

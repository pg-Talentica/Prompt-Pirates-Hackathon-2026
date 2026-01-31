"""Tools invoked by agents: retrieval (RAG), memory read/write, policy checks.

All tool calls are logged (input, execution, result) and emit ToolCallEvent for streaming to UI.

- retrieval_tool(query, k=5): RAG retrieval (observable)
- memory_read_tool, memory_write_tool, memory_read_working_tool, memory_write_working_tool: memory (observable)
- policy_tool(input_text, check_type): guardrails check (observable; Task-006 implements logic)
- observability: wrap_tool, emit_tool_event, register_tool_event_callback, ToolCallEvent
"""

from tools.memory_tools import (
    memory_read_tool,
    memory_read_working_tool,
    memory_write_tool,
    memory_write_working_tool,
)
from tools.observability import (
    ToolCallEvent,
    emit_tool_event,
    register_tool_event_callback,
    unregister_tool_event_callback,
    wrap_tool,
)
from tools.policy_tool import policy_tool, policy_check
from tools.retrieval import get_vector_store, retrieve, retrieval_tool, retrieval_tool_raw

__all__ = [
    "retrieval_tool",
    "retrieval_tool_raw",
    "retrieve",
    "get_vector_store",
    "memory_read_tool",
    "memory_read_working_tool",
    "memory_write_tool",
    "memory_write_working_tool",
    "policy_tool",
    "policy_check",
    "wrap_tool",
    "emit_tool_event",
    "register_tool_event_callback",
    "unregister_tool_event_callback",
    "ToolCallEvent",
]

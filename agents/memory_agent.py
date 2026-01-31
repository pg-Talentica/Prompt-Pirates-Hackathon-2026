"""Memory Agent: manages episodic and semantic memory (read/write via tools).

Reads working memory and optional episodic/semantic; delegates to memory tools.
"""

from __future__ import annotations

import logging
from typing import Any

from agents.state import CoPilotState
from memory.store import MemoryStore
from memory.working_memory import get_working
from tools.memory_tools import memory_read_tool

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "data/memory.db"


def memory_agent(state: CoPilotState) -> dict[str, Any]:
    """Read working memory (and optionally episodic/semantic). Return partial state update."""
    if state.get("escalate"):
        return {}
    session_id = state.get("session_id") or "default"
    store = MemoryStore(db_path=DEFAULT_DB_PATH)

    # Working memory for this session
    working = get_working(store, session_id, limit=20)
    working_formatted = [{"role": r, "content": c} for r, c in working]

    # Episodic/semantic: list recent (optional)
    episodic = memory_read_tool(session_id=None, type_="episodic", limit=5, offset=0)
    semantic = memory_read_tool(session_id=None, type_="semantic", limit=5, offset=0)

    result = {
        "working": working_formatted,
        "episodic": episodic,
        "semantic": semantic,
    }
    logger.info("Memory: working=%d episodic=%d semantic=%d", len(working_formatted), len(episodic), len(semantic))
    return {"memory_result": result}

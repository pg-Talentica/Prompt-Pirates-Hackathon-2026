# Intelligent Support & Incident Co-Pilot

Collaborative agent system for support and operations: ingest tickets and chats, understand intent and risk, retrieve knowledge (RAG), correlate with history, recommend actions, and escalate safely when confidence is low.

**Quick start:** `cp .env.example .env` (set `LLM_API_KEY`), then `docker-compose up`. Open **http://localhost** for the UI and **http://localhost:8000/docs** for the API.

## Repository structure

| Directory | Purpose |
|-----------|--------|
| `api/` | FastAPI application, config, and HTTP/WebSocket entrypoints |
| `agents/` | Agent modules (Ingestion, Planner, Intent, Knowledge Retrieval, Memory, Reasoning, Response Synthesis, Guardrails) |
| `tools/` | Tools invoked by agents (retrieval, memory read/write, policy checks) |
| `memory/` | Memory store (working, episodic, semantic) and persistence |
| `ui/` | React frontend (Vite + TypeScript) and WebSocket client for live streaming |
| `data/` | Knowledge-base corpus (`data/kb/`) and chunking config (`data/chunking.py`) |
| `guardrails/` | Guardrails & safety: content-safety API, confidence thresholds, escalation (Task-006) |
| `scripts/` | Corpus generation and maintenance (e.g. `scripts/generate_corpus.py`) |
| `tasks/` | Task definitions and progress tracking |

Folder and file naming are consistent: one module per agent in `agents/` (e.g. `ingestion.py`, `planner.py`), one module per tool in `tools/` (e.g. `retrieval.py`, `memory_tools.py`), config and schemas in `api/` (`config.py`, `schemas/`), and memory/store in `memory/`.

## Architecture

The pipeline is a **LangGraph**: **Ingestion** → **Planner** → (parallel) **Intent**, **Knowledge Retrieval**, **Memory** → **Reasoning** → **Response Synthesis** → **Guardrails** → **Final Response** or **Escalate**. Serial steps run in order; Intent, Retrieval, and Memory run in parallel after the Planner. Guardrails run twice: after ingestion (input) and before final response (output). See `agents/graph.py` for the graph definition and `agents/state.py` for shared state.

## Where each capability lives

| Capability | Location | Notes |
|------------|----------|--------|
| **RAG** | `tools/retrieval.py`, `tools/vector_store.py`, `agents/knowledge_retrieval.py` | Retrieval tool + Chroma vector store; Knowledge Retrieval Agent calls retrieval before generation. |
| **Chunking** | `data/chunking.py`, `scripts/index_kb.py` | Chunk size/overlap config; indexing script chunks and embeds corpus. |
| **Context** | `memory/working_memory.py`, `agents/state.py` | Working memory per session; bounded context (pruning) for long chats. |
| **Memory** | `memory/store.py`, `memory/service.py`, `tools/memory_tools.py`, `agents/memory_agent.py` | SQLite store (working/episodic/semantic); memory read/write tools; Memory Agent. |
| **Guardrails** | `guardrails/layer.py`, `guardrails/models.py`, `tools/policy_tool.py`, `agents/ingestion.py`, `agents/guardrails_agent.py` | Dual use: after ingestion (input), before final response (output); OpenAI Moderation + config. |
| **Planning** | `agents/planner.py`, `agents/graph.py` | Planner node; graph defines serial/parallel flow. |
| **Tools** | `tools/retrieval.py`, `tools/memory_tools.py`, `tools/policy_tool.py` | Retrieval, memory read/write, policy (guardrails) checks. |
| **Observability** | `tools/observability.py`, `api/routes/chat.py` (WebSocket), `ui/` (stream + metrics) | Tool call events; WebSocket streams agent_step/tool_call; UI shows steps and metrics. |

## Chunking strategy

Documents in `data/kb/` are split into **chunks** with **overlap** for retrieval (RAG).

| Parameter | Value | Rationale |
|-----------|--------|-----------|
| **Chunk size** | 800 characters | Keeps each chunk within a single semantic unit (e.g. a section or a few paragraphs). ~800 chars ≈ 200 tokens, which fits comfortably in typical embedding and LLM context windows while preserving enough context for relevance. |
| **Overlap** | 100 characters | Ensures **semantic continuity** at chunk boundaries: phrases or sentences are not cut mid-way, so retrieval and reasoning see coherent context. Overlap is small enough to avoid excessive duplication and cost. |

- **Retrieval quality:** Medium-sized chunks improve precision (fewer irrelevant spans) and recall (overlap reduces boundary effects).
- **Model context limits:** Chunk size is chosen so that multiple chunks can be passed to the LLM without exceeding context; overlap stays modest to limit token usage.
- **No empirical eval** is required for this task; the values above are justified by common practice and the above rationale. They can be tuned later (e.g. 512/64 or 1024/128) if needed.

Config is defined in `data/chunking.py` and used by the RAG pipeline (Task-003).

## RAG pipeline: retrieval → reasoning → synthesis

The system keeps **retrieval**, **reasoning**, and **response synthesis** clearly separated:

1. **Retrieval** (this task): The Knowledge Retrieval Agent calls the retrieval tool (`tools.retrieval.retrieval_tool`) to fetch top-k chunks from the vector store with source refs (`source_file`, `chunk_index`, `start`, `end`). No generation happens here.
2. **Reasoning** (Task-007): The Reasoning/Correlation Agent consumes the retrieved context plus memory and intent to identify patterns and root causes. It does not call the retrieval tool.
3. **Response synthesis** (Task-007): The Response Synthesis Agent produces the final answer from the reasoning output and **must** reference the retrieved context (enforced by agent design). Generation only happens after retrieval when the KB is used.

Indexing (run once after generating the corpus):

```bash
python scripts/index_kb.py
```

Optional: `--kb-dir data/kb`, `--vector-dir data/vector_store`. Uses `LLM_API_KEY` for OpenAI embeddings, or install `sentence-transformers` for local embeddings without an API key. The vector store is persisted at `data/vector_store/` (Chroma).

## How to run

### With Docker (recommended)

A single command starts the full stack (API + UI). Nginx serves the UI on port 80 and proxies `/api` and WebSocket to the API.

1. Copy environment variables and set required values:
   ```bash
   cp .env.example .env
   # Edit .env and set LLM_API_KEY (required for LLM and optional moderation).
   ```

2. Start the stack:
   ```bash
   docker-compose up
   ```

   - **UI:** http://localhost (nginx serves the built UI; `/api` and `/api/chat/ws` are proxied to the API)
   - **API:** http://localhost:8000 (direct; use for `/docs` and health checks)
   - **API docs:** http://localhost:8000/docs

### Local development

**Backend**

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env, then:
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd ui
npm install
npm run dev
```

- **UI (dev):** http://localhost:5173  
- Vite proxy is configured for `/api` and `/ws` to the backend.

## Config (env only)

All configuration is read from environment variables; no hardcoded secrets or URLs. See [.env.example](.env.example) for the full list.

- **Required:** `LLM_API_KEY` (and optionally `MODEL`) for the LLM provider.  
- **Optional:** `API_HOST`, `API_PORT`, `ENVIRONMENT`, `LOG_LEVEL`, and guardrails vars (see `.env.example`).

Never commit `.env`; it is listed in `.gitignore`. For Docker, use `env_file: .env` (as in `docker-compose.yml`).

## Guardrails (dual use)

Guardrails are applied **twice**; both paths are implemented in `guardrails/` and exposed via `tools.policy_tool` (Guardrails Agent in Task-007):

1. **After ingestion:** Run guardrails on raw user input (`check_input`) to block or escalate before any agent processing if the input is unsafe. Call `policy_check(text, check_type="input")` or `guardrails.check_input(text)`.
2. **Before final response:** Run guardrails on model output (`check_output`) before returning to the user. Block or replace with a safe message if unsafe; supports structured no_answer (“I don’t know”) and escalation policy. Call `policy_check(text, check_type="output")` or `guardrails.check_output(text)`.

Content safety uses the **OpenAI Moderation API** (no hardcoded list of phrases). Config is via env only: `GUARDRAILS_CONFIDENCE_THRESHOLD`, `GUARDRAILS_ESCALATE_ON_NO_ANSWER`, `GUARDRAILS_ESCALATION_POLICY` (JSON). See `.env.example`.

## Knowledge-base corpus

The RAG pipeline uses documents in `data/kb/`. To generate the synthetic corpus (100+ docs, 5–6 pages each):

```bash
python scripts/generate_corpus.py
```

Optional: `--output-dir data/kb` (default), `--count 110`, `--seed 42`, `--txt-only` (skip PDF). With `fpdf2` installed (`pip install fpdf2`), the script also writes `.pdf` versions. Then index for RAG:

```bash
python scripts/index_kb.py
```

## Backend API (chat & WebSocket streaming)

All configuration is via env vars (see `.env.example`).

| Endpoint | Method | Description |
|----------|--------|--------------|
| `/api/chat` | POST | Submit a message/ticket; returns final response or escalation (sync). Body: `{ "query": "...", "session_id": "..." }`. |
| `/api/chat/ws` | WebSocket | Live stream of agent events. Client sends JSON: `{ "query": "...", "session_id": "..." }`. Server sends JSON events: `agent_step`, `tool_call`, `escalation`, `done`, `error`. |
| `/api/sessions` | GET | List session_ids that have working memory (for multi-turn and long-chat support). |
| `/api/memories` | GET/POST/PATCH/DELETE | CRUD for memories (Task-004). |
| `/health` | GET | Health check. |

**WebSocket event schema (stable for UI):** Each event is a JSON object with `type` and optional `agent_id`, `step`, `tool_calls`, `payload`.

- **agent_step:** `{ "type": "agent_step", "agent_id": "<node>", "step": "<node>", "payload": { ... state update } }`
- **tool_call:** `{ "type": "tool_call", "tool_calls": [ { tool_name, input, result, started_at, finished_at, duration_ms, error? } ], "payload": ... }`
- **escalation:** `{ "type": "escalation", "payload": { final_response?, guardrails_result? } }` — conversation/ticket marked as escalated (no external ticket system).
- **done:** `{ "type": "done", "payload": { final_response, escalate, recommended_actions, intent_result?, guardrails_result? } }`
- **error:** `{ "type": "error", "payload": { message, ... } }`

**Session/thread:** Messages are associated with `session_id` for working memory and long-chat support. Working memory is pruned per session (bounded context, 20+ turns). **Escalation** is marked in the API response and in the stream (`escalation` event and `done.payload.escalate`). **Execute path** is stubbed: `recommended_actions` is returned with a note that "execute" is not implemented.

## Frontend (Task-009)

The React UI (`ui/`) provides:

- **Chat:** Single-channel chat; user sends a message, Co-Pilot replies. Session ID is configurable (persisted in `localStorage`). Long chats (20+ turns) stay responsive by rendering the last 100 messages; backend handles context via working-memory pruning.
- **Live stream:** WebSocket connection to `/api/chat/ws`; high-level agent steps (which agent ran) and **expandable** tool call details (input, execution, result) are shown below the chat.
- **Explainability:** Decision reason and evidence snippets (intent result, guardrails result) are shown in a collapsible “Reason & evidence” section per assistant message; no chain-of-thought in the UI.
- **Escalation:** When Guardrails escalate, the assistant message shows an **Escalated** badge and the escalation payload is visible in the stream and in the done event.
- **Memories tab:** List memories (filter by type: working/episodic/semantic), edit content, delete. Uses `GET/PATCH/DELETE /api/memories`.
- **Metrics:** Latency (first event to done), tool call count, and escalation flag are derived from the stream and shown in the Metrics panel.

Run the UI with `cd ui && npm install && npm run dev` (or use Docker). Ensure the API is running so that `/api` and WebSocket `/api/chat/ws` proxy correctly (Vite proxy in `ui/vite.config.ts`).

## Monitoring and metrics

Basic metrics are available in the **UI** (Task-009): **latency** (first stream event to done), **tool call count**, **escalation** (yes/no), and a placeholder for **token usage** (not yet provided by the backend). These are derived from the WebSocket stream; the backend does not expose a separate metrics endpoint. For production, you can add a `/api/metrics` or integrate with your observability stack.

## Testing (Task-010)

Unit tests cover each agent (ingestion, planner, intent, knowledge retrieval, memory, reasoning, response synthesis, guardrails) with mocked LLM and tools. Integration tests exercise the full pipeline: happy path, escalation path, and RAG + memory path. All tests use fixed or mocked data; no live LLM required.

**Run the full test suite:**

```bash
pip install -r requirements.txt   # includes pytest, pytest-asyncio
pytest
```

**Run only unit tests (faster):**

```bash
pytest -m "not integration"
```

**Run only integration flows:**

```bash
pytest -m integration
```

Tests live under `tests/`: `tests/unit/` for per-agent tests, `tests/integration/` for end-to-end flows. See [tasks/Task-010.md](tasks/Task-010.md) for scope.

## Tasks and progress

See [tasks/README.md](tasks/README.md) for the list of high-level tasks and [tasks/progress.md](tasks/progress.md) for completion status.

## License

Internal / hackathon use.

# Intelligent Support & Incident Co-Pilot

Collaborative agent system for support and operations: ingest tickets and chats, understand intent and risk, retrieve knowledge (RAG), correlate with history, recommend actions, and escalate safely when confidence is low.

## Repository structure

| Directory | Purpose |
|-----------|--------|
| `api/` | FastAPI application, config, and HTTP/WebSocket entrypoints |
| `agents/` | Agent modules (Ingestion, Planner, Intent, Knowledge Retrieval, Memory, Reasoning, Response Synthesis, Guardrails) |
| `tools/` | Tools invoked by agents (retrieval, memory read/write, policy checks) |
| `memory/` | Memory store (working, episodic, semantic) and persistence |
| `ui/` | React frontend (Vite + TypeScript) and WebSocket client for live streaming |
| `data/` | Knowledge-base corpus (`data/kb/`) and chunking config (`data/chunking.py`) |
| `scripts/` | Corpus generation and maintenance (e.g. `scripts/generate_corpus.py`) |
| `tasks/` | Task definitions and progress tracking |

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

1. Copy environment variables and set required values:
   ```bash
   cp .env.example .env
   # Edit .env and set LLM_API_KEY and any other values.
   ```

2. Start the stack:
   ```bash
   docker-compose up
   ```

   - **API:** http://localhost:8000  
   - **API docs:** http://localhost:8000/docs  
   - **UI:** http://localhost (after UI container is up)

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

## Environment setup

All configuration is read from environment variables. See [.env.example](.env.example) for the list of variables.

- **Required:** `LLM_API_KEY` (and optionally `MODEL`) for the LLM provider.  
- **Optional:** `API_HOST`, `API_PORT`, `ENVIRONMENT`, `LOG_LEVEL`.

Never commit `.env`; it is listed in `.gitignore`.

## Knowledge-base corpus

The RAG pipeline uses documents in `data/kb/`. To generate the synthetic corpus (100+ docs, 5–6 pages each):

```bash
python scripts/generate_corpus.py
```

Optional: `--output-dir data/kb` (default), `--count 110`, `--seed 42`, `--txt-only` (skip PDF). With `fpdf2` installed (`pip install fpdf2`), the script also writes `.pdf` versions. Then index for RAG:

```bash
python scripts/index_kb.py
```

## Tasks and progress

See [tasks/README.md](tasks/README.md) for the list of high-level tasks and [tasks/progress.md](tasks/progress.md) for completion status.

## License

Internal / hackathon use.

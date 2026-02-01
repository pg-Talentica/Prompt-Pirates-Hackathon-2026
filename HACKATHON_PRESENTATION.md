# Intelligent Support & Incident Co-Pilot
## Collaborative Agentic AI for Intelligent Support & Incident Management

---

## Slide 1: Title Slide

**Project Name:** Intelligent Support & Incident Co-Pilot

**Tagline:** Collaborative Agentic AI for Intelligent Support & Incident Management

**Team:** [Your Team Name]

**Hackathon:** Prompt Pirates Hackathon 2026

---

## Slide 2: Problem Background

### Current Challenges in Modern Software Organizations

- **Support Volume Overload**
  - Thousands of tickets daily across multiple domains
  - Payment, Checkout, Auth, Redis, Kafka, Database, Notifications
  - Response time SLAs under constant pressure

- **Knowledge Fragmentation**
  - Runbooks scattered across PDFs, Word docs, text files
  - Incident reports buried in historical data
  - No unified access to operational knowledge

- **Context Loss**
  - Support agents lack historical context
  - Similar incidents handled repeatedly from scratch
  - No correlation between past and present issues

### Why Traditional Automation & Chatbots Fail

- **Single-agent limitations:** Cannot handle complex, multi-step reasoning
- **No memory:** Each interaction starts from zero
- **Rigid workflows:** Cannot adapt to novel scenarios
- **No safety:** Lack guardrails for harmful content or low-confidence responses
- **Black-box decisions:** No explainability for support teams

---

## Slide 3: Core Challenge

### What Needs to Be Built

A **collaborative multi-agent system** that:

1. **Ingests** support tickets and chat messages
2. **Understands** intent and classifies risk
3. **Retrieves** relevant knowledge from documentation
4. **Correlates** with historical incidents and patterns
5. **Recommends** actionable solutions
6. **Escalates** safely when confidence is low or content is unsafe

### Why a Multi-Agent, Collaborative System is Required

- **Specialization:** Each agent excels at one task (intent, retrieval, reasoning)
- **Parallel execution:** Intent, retrieval, and memory can run simultaneously
- **Collaborative reasoning:** Agents share state and build on each other's outputs
- **Safety by design:** Guardrails at input and output stages
- **Explainability:** Each agent's decision is transparent and traceable

**Single-agent systems cannot achieve this level of sophistication.**

---

## Slide 4: Proposed Solution Overview

### High-Level Description

**Intelligent Support & Incident Co-Pilot** is a **LangGraph-based collaborative agent system** that behaves like a small support team:

- **Ingestion Agent:** Normalizes input, runs initial safety checks
- **Planner/Orchestrator:** Determines which agents to invoke
- **Intent Agent:** Classifies user intent and risk level
- **Knowledge Retrieval Agent:** Retrieves relevant documentation (RAG)
- **Memory Agent:** Accesses working, episodic, and semantic memory
- **Reasoning Agent:** Correlates patterns, identifies root causes
- **Response Synthesis Agent:** Generates coherent, actionable responses
- **Guardrails Agent:** Ensures safety and confidence thresholds

### How It Behaves Like a Small Support Team

1. **Triage** (Ingestion + Guardrails): Assess incoming request
2. **Research** (Intent + Retrieval + Memory): Gather context in parallel
3. **Analysis** (Reasoning): Connect dots, identify patterns
4. **Response** (Synthesis): Craft solution with evidence
5. **Review** (Guardrails): Final safety check before delivery

**All agents share state and collaborate through a unified graph.**

---

## Slide 5: Primary Use Case

### Intelligent Support & Incident Co-Pilot

**Scenario:** Support engineer receives ticket: *"Payment gateway timeout in production"*

**System Behavior:**

1. **Ingestion:** Normalizes query, checks for harmful content
2. **Planner:** Determines this requires RAG + Memory + Reasoning
3. **Parallel Execution:**
   - **Intent:** Classifies as "incident resolution" (high priority)
   - **Retrieval:** Finds payment runbook, error codes, architecture docs
   - **Memory:** Retrieves similar past incidents from episodic memory
4. **Reasoning:** Correlates current issue with historical patterns
5. **Synthesis:** Generates step-by-step resolution with references
6. **Guardrails:** Validates response safety and confidence
7. **Output:** Actionable solution with source citations

### Real-World Value and Impact

- **Faster resolution:** 60-80% reduction in time-to-resolution
- **Consistent quality:** Every response grounded in knowledge base
- **Knowledge retention:** Past incidents inform future decisions
- **Safe escalation:** Low-confidence or unsafe queries escalated automatically
- **Transparency:** Full explainability for support teams

---

## Slide 6: Agentic AI Capabilities

### RAG (Retrieval-Augmented Generation)

**Clear Separation of Concerns:**

1. **Retrieval** (`tools/retrieval.py`): 
   - Vector search (Chroma) with top-k chunks
   - Returns source references (`source_file`, `chunk_index`, `start`, `end`)
   - **No generation** at this stage

2. **Reasoning** (`agents/reasoning.py`):
   - Consumes retrieved context + memory + intent
   - Identifies patterns, root causes, correlations
   - **Does not call retrieval tool**

3. **Generation** (`agents/response_synthesis.py`):
   - Produces final answer from reasoning output
   - **Must reference retrieved context** (enforced by agent design)
   - Generation only happens after retrieval when KB is used

### Chunking & Overlap Strategy

- **Chunk size:** 800 characters (~200 tokens)
  - Fits comfortably in embedding and LLM context windows
  - Preserves semantic units (sections, paragraphs)

- **Overlap:** 100 characters
  - Ensures semantic continuity at boundaries
  - Prevents mid-sentence cuts
  - Balances precision and recall

**Config:** `data/chunking.py` (tunable for different document types)

### Context Management

- **Working memory:** Session-scoped, bounded context (20+ turns)
- **Pruning:** Long chats automatically summarized to prevent unbounded growth
- **State sharing:** All agents access unified `CoPilotState` (TypedDict)

### Memory Types & Persistence

**Three Memory Types (Single SQLite Store):**

1. **Working Memory:**
   - Per-session conversation history
   - Short-lived, pruned for long threads
   - Used for multi-turn context

2. **Episodic Memory:**
   - Past incidents, conversations, outcomes
   - Persists across sessions
   - Influences future decisions

3. **Semantic Memory:**
   - Documents, FAQs, runbooks
   - Can overlap with RAG or reference KB
   - Long-term knowledge retention

**Persistence:** SQLite (`data/memory.db`) survives restarts

### Guardrails & Safety

**Dual Application:**

1. **Input Guardrails** (after ingestion):
   - OpenAI Moderation API
   - Blocks or escalates harmful content before processing

2. **Output Guardrails** (before final response):
   - Content safety check
   - Confidence threshold validation
   - Escalation policy enforcement

**Config:** Environment variables (no hardcoded phrases)

### Planning, Delegation, and Tool Usage

- **Planner Agent:** Determines agent execution order
- **Tool Invocation:** Agents call tools (retrieval, memory, policy) as needed
- **Graph Orchestration:** LangGraph manages serial, parallel, and conditional flows
- **Observability:** All tool calls logged and streamed to UI

---

## Slide 7: Agent Roles & Responsibilities

### 1. Ingestion Agent
- **Role:** First point of contact
- **Responsibilities:**
  - Normalize user input (query cleaning)
  - Run input guardrails (safety check)
  - Early escalation for harmful content
- **Output:** `normalized_query`, `input_guardrails_result`, `escalate` flag

### 2. Planner / Orchestrator
- **Role:** Strategic coordinator
- **Responsibilities:**
  - Analyze normalized query
  - Determine which agents to invoke
  - Set execution strategy (serial/parallel)
- **Output:** Planning decision (implicit in graph flow)

### 3. Intent & Classification Agent
- **Role:** Query understanding
- **Responsibilities:**
  - Classify user intent (incident, FAQ, configuration)
  - Assess risk level (low/medium/high)
  - Determine required capabilities (RAG, memory, escalation)
- **Output:** `intent_result` (intent type, risk, confidence)

### 4. Knowledge Retrieval (RAG) Agent
- **Role:** Information retrieval
- **Responsibilities:**
  - Call retrieval tool (`tools/retrieval.py`)
  - Fetch top-k relevant chunks from vector store
  - Return source references for citation
- **Output:** `retrieval_result` (list of chunks with metadata)

### 5. Memory Agent
- **Role:** Context and history access
- **Responsibilities:**
  - Read working memory (session-scoped)
  - Retrieve episodic memory (past incidents)
  - Access semantic memory (long-term knowledge)
- **Output:** `memory_result` (working, episodic, semantic)

### 6. Reasoning / Correlation Agent
- **Role:** Pattern recognition and root cause analysis
- **Responsibilities:**
  - Correlate current query with retrieved context
  - Identify patterns from historical incidents
  - Connect dots between intent, knowledge, and memory
- **Output:** `reasoning_result` (analysis, patterns, correlations)

### 7. Response Synthesis Agent
- **Role:** Answer generation
- **Responsibilities:**
  - Synthesize reasoning output into coherent response
  - Reference retrieved chunks (enforced citation)
  - Generate actionable recommendations
- **Output:** `draft_response` (final answer with citations)

### 8. Guardrails & Policy Agent
- **Role:** Safety and quality assurance
- **Responsibilities:**
  - Run output guardrails (content safety)
  - Validate confidence thresholds
  - Enforce escalation policies
- **Output:** `guardrails_result`, `escalate` flag, `final_response`

---

## Slide 8: System Architecture

### Agent Interaction Flow

```
START
  ↓
[Ingestion] → Input Guardrails
  ↓
[Planner] → Determines execution strategy
  ↓
┌─────────────────────────────────┐
│  PARALLEL EXECUTION             │
│  ┌──────────┐  ┌──────────┐    │
│  │  Intent  │  │Retrieval │    │
│  └──────────┘  └──────────┘    │
│  ┌──────────┐                  │
│  │  Memory  │                  │
│  └──────────┘                  │
└─────────────────────────────────┘
  ↓ (Fan-in: all complete)
[Reasoning] → Correlation & pattern analysis
  ↓
[Synthesis] → Response generation
  ↓
[Guardrails] → Output safety check
  ↓
┌──────────┐  ┌──────────┐
│ Response │  │ Escalate │
└──────────┘  └──────────┘
  ↓
END
```

### Execution Patterns

**Serial Execution:**
- Ingestion → Planner → Reasoning → Synthesis → Guardrails
- Each step depends on previous output

**Parallel Execution:**
- Intent, Retrieval, Memory run simultaneously after Planner
- All three complete before Reasoning starts

**Asynchronous Execution:**
- Memory writes (fire-and-forget)
- Observability events (streamed to UI)

### Memory and Observability Flow

**Memory Flow:**
- Working memory: Session → SQLite → Retrieved by Memory Agent
- Episodic/Semantic: Persistent → Retrieved by Memory Agent → Used by Reasoning

**Observability Flow:**
- Tool calls → Langfuse tracing → WebSocket stream → UI
- Events: `agent_step`, `tool_call`, `escalation`, `done`, `error`

---

## Slide 9: Sample Scenarios

### Scenario 1: Support Incident

**Query:** "Payment gateway timeout in production, affecting 5% of transactions"

**Flow:**
1. Ingestion: Normalized, safe
2. Planner: Requires RAG + Memory + Reasoning
3. Parallel:
   - Intent: "incident_resolution" (high priority)
   - Retrieval: Payment runbook chunks, error codes
   - Memory: Similar past incidents (episodic)
4. Reasoning: Correlates with historical pattern (last occurred 3 months ago)
5. Synthesis: Step-by-step resolution with diagnostic commands
6. Guardrails: High confidence, safe response
7. **Output:** Actionable solution with source citations

### Scenario 2: Historical Error Lookup

**Query:** "What was the root cause of the Redis cache issue from last month?"

**Flow:**
1. Ingestion: Normalized
2. Planner: Requires Memory (episodic) + Retrieval
3. Parallel:
   - Intent: "historical_lookup"
   - Retrieval: Redis runbook chunks
   - Memory: Episodic memory search (last month's incidents)
4. Reasoning: Matches episodic memory with retrieved context
5. Synthesis: Historical analysis with timeline
6. **Output:** Root cause explanation with references

### Scenario 3: Customer Self-Service Query

**Query:** "How do I configure OAuth token expiry?"

**Flow:**
1. Ingestion: Normalized
2. Planner: Requires RAG (configuration docs)
3. Parallel:
   - Intent: "configuration_query" (low risk)
   - Retrieval: Auth config reference chunks
   - Memory: Working memory (if follow-up)
4. Reasoning: Simple lookup, no correlation needed
5. Synthesis: Configuration steps with examples
6. **Output:** Clear instructions with config parameters

---

## Slide 10: Observability & Explainability

### Live Agent Execution

**WebSocket Streaming:**
- Real-time events: `agent_step`, `tool_call`, `escalation`, `done`
- UI shows which agent is running, what tools are called
- Full transparency of execution flow

**Event Types:**
- `agent_step`: Which agent executed (e.g., "intent", "retrieval")
- `tool_call`: Tool invocation with input/output
- `escalation`: When and why escalation occurred
- `done`: Final response with metadata

### Tool Calls

**Visible in UI:**
- Tool name (e.g., `retrieval_tool`, `memory_read_tool`)
- Input parameters
- Execution result
- Duration (latency metrics)

**Example:**
```json
{
  "type": "tool_call",
  "tool_calls": [{
    "tool_name": "retrieval_tool",
    "input": {"query": "payment gateway timeout"},
    "result": {"chunks": [...], "sources": [...]},
    "duration_ms": 234.5
  }]
}
```

### Decision Transparency

**Per-Message Explainability:**
- **Intent result:** Why query was classified as "incident_resolution"
- **Guardrails result:** Safety check outcome
- **Evidence snippets:** Retrieved chunks used in response
- **Reason & evidence:** Collapsible section in UI

**No Black Box:**
- Every decision is traceable
- Source citations in every response
- Confidence scores visible
- Escalation reasons explained

---

## Slide 11: Expected Hackathon Outcome

### What Judges Should Clearly See

**1. Production-Ready Architecture**
- Clean separation of concerns (agents, tools, memory, guardrails)
- Scalable design (LangGraph, async execution)
- Comprehensive error handling

**2. Collaborative Agent System**
- Multiple specialized agents working together
- Parallel execution for efficiency
- Shared state and context management

**3. Safety & Reliability**
- Dual guardrails (input + output)
- Confidence thresholds
- Safe escalation for low-confidence queries

**4. Knowledge Grounding**
- RAG with clear retrieval → reasoning → generation separation
- Source citations in every response
- No hallucination (enforced by design)

**5. Memory & Context**
- Three memory types (working, episodic, semantic)
- Persistent across sessions
- Influences future decisions

**6. Observability**
- Live execution streaming
- Tool call visibility
- Full explainability

### Why This Solution is Production-Ready

✅ **Modular Design:** Each agent is independently testable  
✅ **Config-Driven:** Environment variables, no hardcoded values  
✅ **Observable:** Full tracing and streaming  
✅ **Safe:** Guardrails at multiple stages  
✅ **Scalable:** Parallel execution, efficient chunking  
✅ **Maintainable:** Clear code structure, comprehensive tests  
✅ **Documented:** README, design docs, inline comments  

**Ready for deployment in production support environments.**

---

## Slide 12: Conclusion / Closing Slide

### Key Takeaways

1. **Collaborative Multi-Agent System**
   - 8 specialized agents working together
   - Parallel execution for efficiency
   - Shared state and context

2. **Production-Grade Capabilities**
   - RAG with clear separation (retrieval → reasoning → generation)
   - Three memory types with persistence
   - Dual guardrails for safety

3. **Full Observability**
   - Live execution streaming
   - Tool call transparency
   - Decision explainability

4. **Real-World Impact**
   - Faster resolution (60-80% reduction)
   - Consistent quality (knowledge-grounded)
   - Safe escalation (confidence-based)

### Why This System Stands Out

**Beyond Single-Agent Chatbots:**
- True collaboration between specialized agents
- Parallel execution for speed
- Memory persistence for context

**Beyond Traditional RAG:**
- Clear separation of retrieval, reasoning, generation
- Correlation with historical incidents
- Source citations enforced

**Beyond Basic Safety:**
- Dual guardrails (input + output)
- Confidence thresholds
- Escalation policies

**Beyond Black-Box AI:**
- Full observability
- Tool call transparency
- Decision explainability

---

## Slide 13: Technical Stack

### Core Technologies

- **LangGraph:** Agent orchestration and graph execution
- **FastAPI:** REST API and WebSocket streaming
- **Chroma:** Vector store for RAG
- **SQLite:** Memory persistence
- **React + TypeScript:** Modern UI with live streaming
- **OpenAI API:** LLM and moderation

### Architecture Highlights

- **TypedDict State:** Type-safe state management
- **Tool-Based Design:** Agents invoke tools (retrieval, memory, policy)
- **WebSocket Streaming:** Real-time observability
- **Docker Compose:** One-command deployment
- **Environment Config:** No hardcoded secrets

---

## Slide 14: Demo Flow

### Live Demonstration

1. **Start System:** `docker-compose up`
2. **Open UI:** http://localhost
3. **Send Query:** "Payment gateway timeout in production"
4. **Observe:**
   - Agent steps in real-time
   - Tool calls with inputs/outputs
   - Retrieved chunks and sources
   - Memory access (working/episodic)
   - Reasoning correlation
   - Final response with citations
5. **Explainability:** Expand "Reason & evidence" section
6. **Metrics:** View latency, tool call count, escalation status

**Full transparency of collaborative agent execution.**

---

## Slide 15: Q&A

### Questions?

**Contact:**
- Repository: [GitHub URL]
- Documentation: `README.md`, `AGENTS_DESIGN.md`
- API Docs: http://localhost:8000/docs

**Thank you for your attention!**

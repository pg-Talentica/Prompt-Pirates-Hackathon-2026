# Tasks Overview

High-level tasks for the **Intelligent Support & Incident Co-Pilot** (Collaborative Agents hackathon). Execute in order where dependencies apply; tasks in the same phase can be parallelized where noted.

| Task | Title | Dependencies |
|------|--------|--------------|
| **Task-001** | Project Setup & Structure | — |
| **Task-002** | Synthetic Dataset & Chunking Strategy | 001 |
| **Task-003** | RAG Pipeline (Indexing & Retrieval) | 001, 002 |
| **Task-004** | Memory System (Store, Persistence, Types) | 001 |
| **Task-005** | Tools Layer & Observable Logging | 003, 004, 006* |
| **Task-006** | Guardrails & Safety (Dual Use + Escalation) | 001 |
| **Task-007** | LangGraph & All Agents | 003, 004, 005, 006 |
| **Task-008** | Backend API (FastAPI & WebSocket Streaming) | 001, 007 |
| **Task-009** | Frontend (React, Live Stream, Memory CRUD, Metrics) | 001, 004, 008 |
| **Task-010** | Testing & QA | 002, 003, 006, 007 |
| **Task-011** | Deployment & Documentation | 001, 002, 008, 009, 010 |

\* Task-005 can stub the policy/guardrails tool and wire it once Task-006 is done.

**Suggested phases:**
- **Phase 1:** 001 (setup)
- **Phase 2:** 002, 004, 006 (data, memory, guardrails in parallel)
- **Phase 3:** 003, 005 (RAG + tools; 005 may stub guardrails)
- **Phase 4:** 007 (LangGraph + agents)
- **Phase 5:** 008, 009 (API + UI in parallel)
- **Phase 6:** 010 (testing), 011 (deploy & docs)

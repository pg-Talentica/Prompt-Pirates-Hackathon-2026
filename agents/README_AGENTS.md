# Separate Agents: Dataset Generator & QA Validation

This document describes the **two completely separate agents** that operate independently from the main Customer Support Agent system.

## Overview

1. **Dataset Generator Agent** - Creates synthetic support knowledge base files
2. **QA/Validation Agent** - Automatically tests the Customer Support Agent

These agents are **completely isolated** and will **NOT** interfere with the main system unless explicitly triggered.

---

## Agent 1: Dataset Generator Agent

### Purpose
Generate a synthetic but realistic support knowledge base for RAG testing.

### Location
- **Module**: `agents/dataset_generator.py`
- **Output**: `data/kb/synthetic/`

### Features
- Generates 100+ files total
- File types: PDF, Word (.docx), TXT, Images (with OCR text)
- Each PDF/Word file: 5-6 pages (~400-500 words per page)
- Domains: Payment, Checkout, Auth, Redis, Kafka, Database, Notifications
- Uses templates + variations (region, environment) to scale

### Usage

#### Generate file list only:
```bash
python -m agents.dataset_generator --list-only --count 100
```

#### Generate complete dataset:
```bash
python -m agents.dataset_generator --output-dir data/kb/synthetic --count 100
```

### Output Structure

```
data/kb/synthetic/
├── dataset_file_list.json          # Complete list of 100+ filenames
└── samples/                        # 10 representative documents
    ├── payment_runbook_001_prod.txt
    ├── checkout_faq_001.txt
    ├── auth_runbook_001_prod.txt
    ├── redis_faq_001.txt
    ├── kafka_runbook_001_prod.txt
    ├── database_faq_001.txt
    ├── notifications_runbook_001_prod.txt
    ├── payment_error_codes_001.txt
    ├── auth_config_reference_001.txt
    └── payment_architecture_diagram_001_ocr.txt
```

### File Distribution
- **PDFs (Runbooks)**: 40 files
- **Word docs (FAQs, SLA policies)**: 30 files
- **TXT files (Error codes, configs)**: 40 files
- **Images (Architecture diagrams)**: 10 files
- **Total**: 120 files

### Content Domains
All content is strictly customer-support related:
- **Payment**: Payment gateway, transactions, refunds
- **Checkout**: Checkout sessions, cart management
- **Auth**: Authentication, OAuth, sessions, tokens
- **Redis**: Cache management, TTL, replication
- **Kafka**: Message queues, consumer lag, brokers
- **Database**: Queries, backups, scaling, replication
- **Notifications**: Email, SMS, push notifications

---

## Agent 2: QA/Validation Agent

### Purpose
Automatically test the behavior of the Customer Support Agent.

### Location
- **Module**: `agents/qa_validation.py`
- **Test Cases**: `tests/qa/test_cases.json`

### Features
- Reads test cases from JSON file
- Executes tests against Customer Support Agent API
- Validates responses against 6 mandatory assertions
- Generates detailed pass/fail reports

### Usage

#### Run QA tests:
```bash
python -m agents.qa_validation \
  --test-cases tests/qa/test_cases.json \
  --api-url http://localhost:8000 \
  --output-report tests/qa/report.json
```

### Test Case Format

Each test case in `test_cases.json` includes:
- `id`: Unique test identifier
- `query`: Test query to send to Customer Support Agent
- `expected_behavior`: `"answer"` | `"no_answer"` | `"escalate"`
- `expected_guardrail`: Optional guardrail type (e.g., `"content_safety"`)
- `should_use_rag`: Optional boolean (should RAG be used?)
- `should_use_memory`: Optional boolean (should memory be used?)
- `description`: Human-readable test description

### Mandatory Assertions

#### 1. RAG Grounding
- If `expected_behavior == "answer"`: `rag_docs_used > 0`
- If `expected_behavior == "no_answer"`: `rag_docs_used == 0`

#### 2. Hallucination Prevention
- If `rag_docs_used == 0`: `final_action MUST be "no_answer"`

#### 3. Out-of-Scope Enforcement
- General knowledge, creative, or future queries MUST result in `"no_answer"`

#### 4. Guardrails
- If `expected_guardrail` is defined:
  - `guardrails_triggered == true`
  - `final_action == "escalate"`

#### 5. Memory
- If `should_use_memory == true`: `memory_used == true`

#### 6. Planning
- For complex queries, assert multiple agents ran (Intent + RAG + Memory)

### Output Report

The QA agent generates a JSON report with:
- Summary: total tests, passed, failed, pass rate
- Failure reasons: grouped by assertion type
- Per-test results: pass/fail status, failures, execution time

Example report:
```json
{
  "summary": {
    "total_tests": 25,
    "passed": 23,
    "failed": 2,
    "pass_rate": "92.0%"
  },
  "failure_reasons": {
    "RAG Grounding failed": 1,
    "Hallucination Prevention failed": 1
  },
  "test_results": [...]
}
```

---

## Separation from Main System

### Key Points

1. **No Integration**: These agents are NOT part of the main Customer Support Agent graph
2. **Separate Execution**: They run as standalone scripts, not triggered by UI or API calls
3. **No State Sharing**: They don't share state with the main system
4. **Independent Testing**: QA agent tests the main system via HTTP API only

### How to Ensure Separation

1. **Dataset Generator**:
   - Only runs when explicitly called: `python -m agents.dataset_generator`
   - Writes to separate directory: `data/kb/synthetic/`
   - Does NOT modify existing KB files

2. **QA Validation**:
   - Only runs when explicitly called: `python -m agents.qa_validation`
   - Reads test cases from `tests/qa/test_cases.json`
   - Tests main system via HTTP API (`POST /api/chat`)
   - Does NOT modify production logic

### Verification

To verify these agents don't interfere:
1. Run main system: `docker-compose up`
2. Use UI normally - Dataset Generator and QA agents are NOT triggered
3. Only when you explicitly run them do they execute

---

## Example Workflow

### Step 1: Generate Dataset
```bash
# Generate synthetic knowledge base
python -m agents.dataset_generator \
  --output-dir data/kb/synthetic \
  --count 100

# Index the synthetic KB (optional, for testing)
python scripts/index_kb.py --kb-dir data/kb/synthetic
```

### Step 2: Run QA Tests
```bash
# Ensure main system is running
docker-compose up -d

# Run QA validation
python -m agents.qa_validation \
  --test-cases tests/qa/test_cases.json \
  --api-url http://localhost:8000 \
  --output-report tests/qa/report.json
```

### Step 3: Review Results
```bash
# View report
cat tests/qa/report.json | jq '.summary'
```

---

## Notes

- These agents are **completely separate** from the main Customer Support Agent
- They are **NOT** triggered by normal UI or API usage
- They only run when **explicitly invoked** via command line
- They follow the **hackathon problem statement** requirements exactly

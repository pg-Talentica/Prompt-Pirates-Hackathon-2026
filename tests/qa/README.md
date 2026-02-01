# QA/Validation Agent (Agent 3)

## Overview

The QA/Validation Agent is a fully automated black-box testing system for the Customer Support Agent. It validates agent behavior without reading dataset files directly and tests the agent through its API or internal interface.

## Key Features

- **Black-Box Testing**: Does NOT read dataset files directly
- **Comprehensive Assertions**: Validates RAG grounding, hallucination prevention, out-of-scope enforcement, guardrails, memory usage, and agentic planning
- **Dual Mode**: Can use HTTP API or direct graph invocation
- **Detailed Reports**: Generates both JSON (machine-readable) and console (human-readable) reports
- **Completely Separate**: Does not interfere with main system or UI operations

## Mandatory Assertions

The QA Agent automatically validates:

1. **RAG Grounding**
   - If `expected_behavior == "answer"`: asserts `rag_docs_used > 0`
   - If `expected_behavior == "no_answer"`: asserts `rag_docs_used == 0`

2. **Hallucination Prevention**
   - If `rag_docs_used == 0`: asserts `final_action == "no_answer"` with explicit uncertainty message

3. **Out-of-Scope Enforcement**
   - General knowledge, creative, future, or unrelated queries MUST result in `no_answer`

4. **Guardrails & Escalation**
   - If `expected_guardrail` is defined: asserts guardrails triggered and `final_action == "escalate"`

5. **Memory Usage**
   - If `should_use_memory == true`: asserts `memory_used == true`

6. **Agentic Planning**
   - For complex queries: asserts required agents ran (IntentAgent, RAGAgent, etc.)

## Test Case Format

Each test case in `test_cases.json` contains:

```json
{
  "id": "TC001",
  "description": "Test case description",
  "query": "User query to test",
  "expected_behavior": "answer" | "no_answer" | "escalate",
  "expected_guardrail": "content_safety" (optional),
  "should_use_rag": true | false (optional),
  "should_use_memory": true | false (optional)
}
```

## Usage

### Basic Usage (Direct Graph Invocation)

```bash
# Run all test cases
python scripts/run_qa_validation.py

# With custom test cases file
python scripts/run_qa_validation.py --test-cases tests/qa/test_cases.json

# With custom output directory
python scripts/run_qa_validation.py --output-dir tests/qa/reports

# Verbose logging
python scripts/run_qa_validation.py --verbose
```

### API Mode (True Black-Box)

```bash
# Use HTTP API instead of direct graph invocation
python scripts/run_qa_validation.py --use-api --api-url http://localhost:8000
```

### Command Line Options

```
--test-cases PATH     Path to test cases JSON file (default: tests/qa/test_cases.json)
--output-dir PATH     Directory for output reports (default: tests/qa/reports)
--api-url URL         API URL (if using --use-api)
--use-api             Use HTTP API instead of direct graph invocation
--verbose             Enable verbose logging
```

## Output

### JSON Report

Machine-readable report saved to `tests/qa/reports/qa_report_YYYYMMDD_HHMMSS.json`:

```json
{
  "timestamp": "2026-02-01T12:00:00.000000",
  "summary": {
    "total_tests": 20,
    "passed": 18,
    "failed": 2,
    "breakdown": {
      "hallucination": 0,
      "rag_missing": 1,
      "out_of_scope_violation": 1,
      "guardrail_failure": 0,
      "memory_failure": 0,
      "execution_error": 0
    },
    "execution_time_ms": 45230.5
  },
  "test_results": [...]
}
```

### Console Report

Human-readable summary printed to console:

```
================================================================================
QA VALIDATION REPORT
================================================================================

Timestamp: 2026-02-01T12:00:00.000000

Summary:
  Total Tests: 20
  Passed: 18 (90.0%)
  Failed: 2 (10.0%)
  Execution Time: 45230 ms

Failure Breakdown:
  - rag_missing: 1
  - out_of_scope_violation: 1

================================================================================
DETAILED RESULTS
================================================================================

[✓ PASS] TC001
  Query: What's the loan policy for a student in 12th and want to study abroad...
  Expected: answer
  Actual: answer
  Execution Time: 2150 ms

[✗ FAIL] TC010
  Query: What will happen to education loan interest rates next year?
  Expected: no_answer
  Actual: answer
  Execution Time: 2100 ms
  Failed Rules: Out_of_Scope_Enforcement, Expected_Behavior_Match
    - Out_of_Scope_Enforcement: Out-of-scope query must return no_answer. Got answer
    - Expected_Behavior_Match: Expected no_answer, got answer
```

## Integration

The QA Agent is completely separate from the main system:

- **No UI Integration**: Does not appear in or interfere with the UI
- **No API Endpoints**: Does not expose any API endpoints
- **Standalone Execution**: Runs only when explicitly invoked via script
- **No Side Effects**: Does not modify production logic or data

## Example Test Cases

See `test_cases.json` for education loan domain test cases covering:

- Valid education loan queries (should use RAG)
- Out-of-scope queries (should return no_answer)
- Harmful content (should trigger guardrails and escalate)
- Complex queries (should use multiple agents)

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

This allows integration with CI/CD pipelines:

```bash
python scripts/run_qa_validation.py && echo "All tests passed" || echo "Tests failed"
```

## Architecture

```
QA Agent (Agent 3)
    │
    ├── Loads test cases from JSON
    │
    ├── For each test case:
    │   ├── Invokes Customer Support Agent (black-box)
    │   ├── Captures full structured response
    │   └── Runs mandatory assertions
    │
    └── Generates reports (JSON + Console)
```

## Non-Goals (Strict)

The QA Agent MUST NOT:
- Read or parse dataset files
- Generate answers
- Modify production logic
- Depend on UI interactions
- Bypass RAG or guardrails
- Interfere with normal system operations

## Troubleshooting

### Tests failing unexpectedly

1. Check if Customer Support Agent is running (if using API mode)
2. Verify test cases match current agent behavior
3. Check logs with `--verbose` flag
4. Review assertion results in JSON report

### API mode limitations

When using `--use-api`, some information may not be available:
- `rag_docs_used`: May be 0 (unknown from API)
- `memory_used`: May be False (unknown from API)
- `agents_ran`: May be empty (unknown from API)

For full validation, use direct graph invocation (default mode).

## See Also

- `agents/qa_validation.py`: QA Agent implementation
- `tests/qa/test_cases.json`: Test cases
- `tests/qa/example_qa_report.json`: Example report output

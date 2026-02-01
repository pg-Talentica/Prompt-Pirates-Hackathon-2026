# Quick Start: Two Separate Agents

## Overview

Two completely separate agents that operate independently from the main Customer Support Agent:

1. **Dataset Generator Agent** - Creates 100+ synthetic support KB files
2. **QA/Validation Agent** - Tests Customer Support Agent behavior

---

## 1. Dataset Generator Agent

### Generate File List
```bash
python -m agents.dataset_generator --list-only --count 100
```

Output: `data/kb/synthetic/dataset_file_list.json`

### Generate Complete Dataset
```bash
python -m agents.dataset_generator \
  --output-dir data/kb/synthetic \
  --count 100
```

Output:
- File list: `data/kb/synthetic/dataset_file_list.json`
- Sample content: `data/kb/synthetic/samples/` (10 representative documents)

### File Distribution
- **PDFs**: 40 files (runbooks)
- **Word docs**: 30 files (FAQs, SLA policies)
- **TXT**: 40 files (error codes, configs)
- **Images**: 10 files (architecture diagrams with OCR)
- **Total**: 120 files

---

## 2. QA/Validation Agent

### Prerequisites
Ensure main Customer Support Agent is running:
```bash
docker-compose up -d
# Or: uvicorn api.main:app --reload
```

### Run QA Tests
```bash
python -m agents.qa_validation \
  --test-cases tests/qa/test_cases.json \
  --api-url http://localhost:8000 \
  --output-report tests/qa/report.json
```

### Test Cases
Location: `tests/qa/test_cases.json`
- 25 test cases covering:
  - RAG usage scenarios
  - Out-of-scope queries
  - Guardrails/escalation
  - Memory usage
  - Complex queries

### Output
- Console: Pass/fail summary with details
- JSON Report: `tests/qa/report.json` (if `--output-report` specified)

---

## Verification

### Check Separation
1. Start main system: `docker-compose up`
2. Use UI normally - agents are NOT triggered
3. Only run when explicitly called

### Test Dataset Generator
```bash
python -m agents.dataset_generator --list-only
# Should output file list without errors
```

### Test QA Agent
```bash
# Ensure main system is running first
python -m agents.qa_validation \
  --test-cases tests/qa/test_cases.json \
  --api-url http://localhost:8000
# Should run tests and show results
```

---

## Files Created

### Dataset Generator
- `agents/dataset_generator.py` - Main agent module
- `data/kb/synthetic/dataset_file_list.json` - File list (after running)
- `data/kb/synthetic/samples/` - Sample content (after running)

### QA Validation
- `agents/qa_validation.py` - Main agent module
- `tests/qa/test_cases.json` - Test cases (25 tests)
- `tests/qa/report.json` - Test report (after running)

### Documentation
- `agents/README_AGENTS.md` - Detailed documentation
- `AGENTS_DESIGN.md` - Design document
- `QUICK_START_AGENTS.md` - This file

---

## Key Points

✅ **Completely Separate**: Not part of main Customer Support Agent
✅ **Explicit Execution**: Only run when explicitly called
✅ **No Interference**: Don't affect normal UI/API usage
✅ **All Requirements Met**: 100+ files, 6 assertions, test cases

---

## Next Steps

1. **Generate Dataset**: Run Dataset Generator to create synthetic KB
2. **Index Dataset** (optional): `python scripts/index_kb.py --kb-dir data/kb/synthetic`
3. **Run QA Tests**: Execute QA Validation Agent to test main system
4. **Review Results**: Check test report for pass/fail status

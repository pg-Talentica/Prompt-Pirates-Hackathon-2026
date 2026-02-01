# QA Agent Testing Guide - Quick Reference

## 🚀 Quick Start

### Run All Tests

```bash
# Simple run
python scripts/run_qa_validation.py

# Or use the quick test script
bash scripts/quick_qa_test.sh
```

## 📋 What You'll See

### 1. Console Output (Real-time)

As tests run, you'll see:
- Progress for each test case
- Pass/fail status
- Summary statistics
- Failure breakdown

### 2. JSON Report (Saved)

Detailed report saved to:
```
tests/qa/reports/qa_report_YYYYMMDD_HHMMSS.json
```

## 📊 Understanding Results

### Test Status

- **✓ PASS**: All assertions passed
- **✗ FAIL**: One or more assertions failed

### Summary Metrics

- **Total Tests**: Number of test cases run
- **Passed**: Count and percentage of passing tests
- **Failed**: Count and percentage of failing tests
- **Execution Time**: Total time to run all tests
- **Failure Breakdown**: Count by failure type

### Failure Types

- **hallucination**: Answered without RAG docs
- **rag_missing**: Expected RAG but none used
- **out_of_scope_violation**: Answered out-of-scope query
- **guardrail_failure**: Guardrails didn't trigger
- **memory_failure**: Memory not used when required
- **execution_error**: Test execution error

## 🔍 Viewing Detailed Results

### View JSON Report

```bash
# Pretty print latest report
cat tests/qa/reports/qa_report_*.json | python3 -m json.tool | less

# Or with jq (if installed)
cat tests/qa/reports/qa_report_*.json | jq .
```

### View Summary Only

```bash
# Extract summary
python3 -c "
import json
import glob
report = max(glob.glob('tests/qa/reports/qa_report_*.json'), key=os.path.getctime)
with open(report) as f:
    data = json.load(f)
    print(json.dumps(data['summary'], indent=2))
"
```

## 🎯 Testing Modes

### Mode 1: Direct Graph (Default)

Tests agent directly - fastest, most detailed:

```bash
python scripts/run_qa_validation.py
```

**Pros:**
- Fast execution
- Full state information available
- No API server needed

### Mode 2: API Mode (True Black-Box)

Tests through HTTP API:

```bash
# Start API first
docker-compose up -d api

# Then test
python scripts/run_qa_validation.py --use-api --api-url http://localhost:8000
```

**Pros:**
- True black-box testing
- Tests actual API endpoint
- More realistic production testing

## 📈 Example Output

### Successful Run

```
================================================================================
QA VALIDATION REPORT
================================================================================

Summary:
  Total Tests: 20
  Passed: 20 (100.0%)
  Failed: 0 (0.0%)
  Execution Time: 45000 ms

[✓ PASS] TC001 - Education loan eligibility query
[✓ PASS] TC002 - Loan eligibility for international studies
...
```

### Run with Failures

```
================================================================================
QA VALIDATION REPORT
================================================================================

Summary:
  Total Tests: 20
  Passed: 18 (90.0%)
  Failed: 2 (10.0%)
  Execution Time: 45230 ms

Failure Breakdown:
  - rag_missing: 1
  - out_of_scope_violation: 1

[✗ FAIL] TC010
  Query: What will happen to education loan interest rates next year?
  Expected: no_answer
  Actual: answer
  Failed Rules: Out_of_Scope_Enforcement, Expected_Behavior_Match
```

## 🛠️ Troubleshooting

### Tests Not Running

```bash
# Check dependencies
pip install -r requirements.txt

# Check test cases file
ls -lh tests/qa/test_cases.json

# Run with verbose
python scripts/run_qa_validation.py --verbose
```

### API Mode Not Working

```bash
# Check if API is running
curl http://localhost:8000/health

# Or check Docker
docker-compose ps api
```

### Slow Execution

- Normal: 20-60 seconds for 20 tests
- If slower: Check vector store indexing
- Use `--verbose` to see which tests are slow

## 📝 Customization

### Run Subset of Tests

Edit `tests/qa/test_cases.json` to include only desired tests, then run:

```bash
python scripts/run_qa_validation.py --test-cases tests/qa/test_cases.json
```

### Custom Output Location

```bash
python scripts/run_qa_validation.py --output-dir /custom/path/reports
```

## 🎓 Best Practices

1. **Run regularly**: After code changes
2. **Review failures**: Check assertion results in JSON
3. **Fix systematically**: Address failures by type
4. **Re-test**: Verify fixes with another run
5. **Track trends**: Compare reports over time

## 📦 Integration

### CI/CD Pipeline

```yaml
# Example GitHub Actions
- name: Run QA Validation
  run: |
    python scripts/run_qa_validation.py
    # Exit code 0 = pass, 1 = fail
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
python scripts/run_qa_validation.py
if [ $? -ne 0 ]; then
  echo "QA tests failed - commit blocked"
  exit 1
fi
```

## 🎯 Quick Commands Reference

```bash
# Basic run
python scripts/run_qa_validation.py

# With verbose logging
python scripts/run_qa_validation.py --verbose

# API mode
python scripts/run_qa_validation.py --use-api

# Custom test cases
python scripts/run_qa_validation.py --test-cases custom.json

# Quick test script
bash scripts/quick_qa_test.sh

# View latest report
cat tests/qa/reports/qa_report_*.json | python3 -m json.tool | less
```

## ✅ Success Criteria

A successful QA run means:
- All test cases pass
- RAG grounding works correctly
- Hallucination prevention is effective
- Out-of-scope queries are rejected
- Guardrails trigger appropriately
- Memory usage works when needed

## 🚀 Next Steps

1. **Run the QA agent**: `python scripts/run_qa_validation.py`
2. **Review results**: Check console and JSON reports
3. **Address failures**: Fix any issues in Customer Support Agent
4. **Re-run**: Verify fixes
5. **Integrate**: Add to your workflow

Happy testing! 🎉

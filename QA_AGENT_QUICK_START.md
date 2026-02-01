# QA Agent - Quick Start Guide

## 🎯 Run QA Tests in 3 Steps

### Step 1: Run the QA Agent

```bash
python scripts/run_qa_validation.py
```

**OR use the quick script:**

```bash
bash scripts/quick_qa_test.sh
```

### Step 2: View Results

Results appear in **two places**:

1. **Console** (immediate output)
2. **JSON Report** (saved to `tests/qa/reports/qa_report_*.json`)

### Step 3: Interpret Results

- **✓ PASS**: Test passed all assertions
- **✗ FAIL**: Test failed one or more assertions
- **Summary**: Shows total passed/failed and breakdown

## 📊 What You'll See

### Console Output Example

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
  Query: What's the loan policy for a student in 12th...
  Expected: answer
  Actual: answer
  Execution Time: 2150 ms

[✗ FAIL] TC010
  Query: What will happen to education loan interest rates next year?
  Expected: no_answer
  Actual: answer
  Execution Time: 2100 ms
  Failed Rules: Out_of_Scope_Enforcement, Expected_Behavior_Match
```

### JSON Report Location

```
tests/qa/reports/qa_report_20260201_120000.json
```

## 🔧 Common Commands

### Basic Test Run
```bash
python scripts/run_qa_validation.py
```

### Verbose Output (See Details)
```bash
python scripts/run_qa_validation.py --verbose
```

### Test via API (Black-Box)
```bash
# First, ensure API is running
docker-compose up -d api

# Then test
python scripts/run_qa_validation.py --use-api --api-url http://localhost:8000
```

### View Latest Report
```bash
# List reports
ls -lh tests/qa/reports/

# View latest (with jq if installed)
cat tests/qa/reports/qa_report_*.json | jq .summary

# Or with Python
python3 -c "
import json, glob, os
report = max(glob.glob('tests/qa/reports/qa_report_*.json'), key=os.path.getctime)
with open(report) as f:
    data = json.load(f)
    import json as j
    print(j.dumps(data['summary'], indent=2))
"
```

## 📈 Understanding Results

### Test Passes When:
- ✅ All assertions pass
- ✅ `final_action` matches `expected_behavior`
- ✅ RAG usage is correct
- ✅ Guardrails work (if applicable)

### Test Fails When:
- ❌ Any assertion fails
- ❌ Wrong behavior (e.g., answered when should say "no_answer")
- ❌ RAG not used when expected
- ❌ Guardrails didn't trigger

### Failure Types:
- **hallucination**: Answered without RAG docs
- **rag_missing**: Expected RAG but none used
- **out_of_scope_violation**: Answered out-of-scope query
- **guardrail_failure**: Guardrails didn't trigger
- **memory_failure**: Memory not used when required

## 🎓 Example Workflow

```bash
# 1. Run tests
python scripts/run_qa_validation.py

# 2. Check summary
# Look for: "Passed: X (Y%)"

# 3. If failures, check details
cat tests/qa/reports/qa_report_*.json | jq '.test_results[] | select(.passed == false)'

# 4. Fix issues in Customer Support Agent

# 5. Re-run
python scripts/run_qa_validation.py
```

## 🚀 Quick Demo

Try running a quick test:

```bash
# Run with verbose to see what's happening
python scripts/run_qa_validation.py --verbose 2>&1 | head -50
```

## 📝 Files Created

After running, you'll have:

- **Console output**: Printed during execution
- **JSON report**: `tests/qa/reports/qa_report_YYYYMMDD_HHMMSS.json`

## ✅ Success Indicators

- **Exit code 0**: All tests passed ✅
- **Exit code 1**: Some tests failed ❌
- **Summary shows 100% pass**: Perfect! 🎉
- **Summary shows < 100%**: Review failures

## 🎯 Next Steps

1. **Run**: `python scripts/run_qa_validation.py`
2. **Review**: Check console and JSON reports
3. **Fix**: Address any failures
4. **Re-test**: Verify fixes
5. **Integrate**: Add to CI/CD

That's it! The QA agent will validate your Customer Support Agent automatically. 🚀

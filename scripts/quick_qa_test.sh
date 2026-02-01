#!/bin/bash
# Quick QA Test Script - Run QA validation and show results

set -e

echo "=========================================="
echo "QA Agent - Quick Test"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Check if test cases exist
if [ ! -f "tests/qa/test_cases.json" ]; then
    echo "Error: Test cases file not found: tests/qa/test_cases.json"
    exit 1
fi

echo "Running QA validation..."
echo ""

# Run QA agent
python3 scripts/run_qa_validation.py --output-dir tests/qa/reports

# Get exit code
EXIT_CODE=$?

echo ""
echo "=========================================="
echo "QA Test Complete"
echo "=========================================="
echo ""

# Show latest report file
LATEST_REPORT=$(ls -t tests/qa/reports/qa_report_*.json 2>/dev/null | head -1)

if [ -n "$LATEST_REPORT" ]; then
    echo "📊 JSON Report: $LATEST_REPORT"
    echo ""
    echo "Summary from report:"
    python3 -c "
import json
import sys
try:
    with open('$LATEST_REPORT', 'r') as f:
        data = json.load(f)
    summary = data['summary']
    print(f\"  Total Tests: {summary['total_tests']}\")
    print(f\"  Passed: {summary['passed']} ({summary['passed']/summary['total_tests']*100:.1f}%)\")
    print(f\"  Failed: {summary['failed']} ({summary['failed']/summary['total_tests']*100:.1f}%)\")
    print(f\"  Execution Time: {summary['execution_time_ms']:.0f} ms\")
    if summary.get('breakdown'):
        print(f\"  Failure Breakdown:\")
        for k, v in summary['breakdown'].items():
            if v > 0:
                print(f\"    - {k}: {v}\")
except Exception as e:
    print(f\"  Error reading report: {e}\")
    sys.exit(1)
" 2>/dev/null || echo "  (Install python3 to view summary)"
else
    echo "⚠ No report file found"
fi

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed. Check the report for details."
fi

exit $EXIT_CODE

#!/bin/bash
# Re-run project: Re-index knowledge base and verify RAG setup

set -e

echo "=========================================="
echo "Re-running Project - RAG Setup"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Step 1: Install dependencies if needed
echo "Step 1: Checking dependencies..."
if ! python3 -c "import pydantic" 2>/dev/null; then
    echo "Installing dependencies from requirements.txt..."
    pip3 install -r requirements.txt
else
    echo "✓ Dependencies already installed"
fi
echo ""

# Step 2: Re-index knowledge base
echo "Step 2: Re-indexing knowledge base..."
python3 scripts/index_kb.py --clear
echo ""

# Step 3: Verify RAG setup
echo "Step 3: Verifying RAG setup..."
python3 scripts/verify_rag_setup.py
echo ""

# Step 4: Test with user query
echo "Step 4: Testing with user query..."
python3 scripts/diagnose_retrieval.py
echo ""

echo "=========================================="
echo "Re-run complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start the API server: uvicorn api.main:app --reload"
echo "2. Or test via API: curl -X POST http://localhost:8000/api/chat -H 'Content-Type: application/json' -d '{\"query\": \"What'\''s the loan policy for a student in 12th and want to study abroad in science field.\", \"session_id\": \"test123\"}'"

# Quick Re-Run Guide

## Step 1: Install Dependencies (if not already installed)

```bash
pip install -r requirements.txt
```

Or install key dependencies:
```bash
pip install pydantic pydantic-settings chromadb openai pypdf fastapi uvicorn langgraph langfuse
```

## Step 2: Re-Index Knowledge Base

Clear and re-index all documents:

```bash
python scripts/index_kb.py --clear
```

This will:
- Clear the existing vector store
- Index all `.txt` and `.pdf` files from `data/kb/hackathon_dataset/`
- Create embeddings for all chunks

**Note**: Make sure you have `LLM_API_KEY` set in your `.env` file for better embeddings. If not set, it will use a fallback model.

## Step 3: Verify Setup

Run the verification script:

```bash
python scripts/verify_rag_setup.py
```

This checks:
- Vector store has data
- Retrieval works
- Configuration is correct

## Step 4: Test with Your Query

Test retrieval with your specific query:

```bash
python scripts/diagnose_retrieval.py
```

Or use the Python interpreter:

```python
from tools.retrieval import retrieve

results = retrieve("What's the loan policy for a student in 12th and want to study abroad in science field.", k=8)
print(f"Found {len(results)} results")
for r in results[:3]:
    print(f"\nSource: {r.get('source_file')}")
    print(f"Distance: {r.get('distance')}")
    print(f"Text: {r.get('text', '')[:200]}...")
```

## Step 5: Start the API Server

```bash
uvicorn api.main:app --reload
```

Then test via API:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What'\''s the loan policy for a student in 12th and want to study abroad in science field.", "session_id": "test123"}'
```

## Or Use the Automated Script

Run the automated re-run script:

```bash
# Python version (recommended)
python scripts/rerun_project.py

# Or shell script version
bash scripts/rerun_project.sh
```

## Troubleshooting

### If indexing fails:
1. Check if `pypdf` is installed: `pip install pypdf`
2. Verify PDF files are readable
3. Check `.env` file has `LLM_API_KEY` set

### If retrieval returns no results:
1. Verify vector store has data: Check `data/vector_store/chroma.sqlite3` exists and has size > 0
2. Check logs for indexing errors
3. Try simpler query: `"education loan eligibility"`

### If distances are too high:
1. Check `.env` for `RAG_MAX_DISTANCE` and `RAG_CONFIDENCE_MAX_DISTANCE`
2. Defaults are now 1.5 and 1.3 (more lenient)
3. Consider re-indexing with better chunking

## Expected Output

After re-indexing, you should see:
```
INFO Indexed X chunks from data/kb/hackathon_dataset into data/vector_store
```

After verification:
```
✓ Vector store has X chunks
✓ Retrieval successful: 5 results, best distance 0.XXXX
```

After testing:
```
Retrieved 8 chunks for query: ...
Top sources: Eligibility_Documents/..., Loan_Policy/...
```

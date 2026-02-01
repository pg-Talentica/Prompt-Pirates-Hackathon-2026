# Re-Run Project Instructions

## Quick Start

Since dependencies need to be installed first, here's the step-by-step process:

### 1. Install Dependencies

```bash
cd /Users/raghunandan/Documents/Prompt-Pirates-Hackathon-2026
pip install -r requirements.txt
```

Key dependencies needed:
- `pydantic` & `pydantic-settings`
- `chromadb`
- `openai`
- `pypdf` (for PDF indexing)
- `fastapi` & `uvicorn`
- `langgraph`

### 2. Set Environment Variables

Create or update `.env` file in project root:

```env
LLM_API_KEY=your_openai_api_key_here
RAG_MAX_DISTANCE=1.5
RAG_CONFIDENCE_MAX_DISTANCE=1.3
```

### 3. Re-Index Knowledge Base

```bash
python scripts/index_kb.py --clear
```

This will:
- ✅ Clear existing vector store
- ✅ Index all PDF and TXT files from `data/kb/hackathon_dataset/`
- ✅ Create embeddings for retrieval

**Expected output:**
```
INFO Indexed X chunks from data/kb/hackathon_dataset into data/vector_store
```

### 4. Verify Everything Works

```bash
# Verify RAG setup
python scripts/verify_rag_setup.py

# Test with your query
python scripts/diagnose_retrieval.py
```

### 5. Start the Server

```bash
uvicorn api.main:app --reload
```

### 6. Test the Query

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What'\''s the loan policy for a student in 12th and want to study abroad in science field.",
    "session_id": "test123"
  }'
```

Or use the automated script:

```bash
python scripts/rerun_project.py
```

## What Was Fixed

1. **Distance Thresholds**: Increased from 1.2/1.1 to 1.5/1.3 (more lenient)
2. **Query Expansion**: Added fallback queries for education loan topics
3. **Better Logging**: Added detailed diagnostics
4. **Lenient Relevance**: Education loan queries get 20% more lenient threshold

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pydantic'"
**Solution**: Install dependencies: `pip install -r requirements.txt`

### Issue: "No results returned" or "I don't have information"
**Solution**: 
1. Re-index: `python scripts/index_kb.py --clear`
2. Check if PDFs are readable (need `pypdf`)
3. Verify `LLM_API_KEY` is set in `.env`

### Issue: "Vector store is empty"
**Solution**: 
1. Check `data/kb/hackathon_dataset/` has files
2. Run indexing: `python scripts/index_kb.py --clear`
3. Check logs for errors

### Issue: High distances (> 1.5)
**Solution**:
1. Ensure `LLM_API_KEY` is set (better embeddings)
2. Check if documents are properly indexed
3. Try re-indexing

## Files Modified

- `agents/knowledge_retrieval.py` - Query expansion
- `agents/response_synthesis.py` - Lenient thresholds
- `tools/retrieval.py` - Better logging
- `api/config.py` - Increased default thresholds
- `agents/ingestion.py` - Preserve query case

## New Diagnostic Tools

- `scripts/diagnose_retrieval.py` - Test retrieval
- `scripts/verify_rag_setup.py` - Verify setup
- `scripts/rerun_project.py` - Automated re-run

## Expected Behavior

After re-indexing and with the fixes:
- ✅ Queries about education loans should retrieve relevant chunks
- ✅ Distance thresholds are more lenient (1.5/1.3)
- ✅ Query expansion helps with edge cases
- ✅ Better logging for debugging

The query "What's the loan policy for a student in 12th and want to study abroad in science field" should now:
1. Retrieve relevant chunks from eligibility documents
2. Pass the distance threshold check
3. Generate a proper response based on retrieved context

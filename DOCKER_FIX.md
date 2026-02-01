# Docker Compose Fix - LLM_API_KEY Issue

## Problem
The vector store was not finding `LLM_API_KEY` even though it was set in `.env` file.

## Solution Applied

### 1. Updated Docker Entrypoint (`scripts/docker_entrypoint.py`)
- ✅ Explicitly checks for `LLM_API_KEY` in environment variables first
- ✅ Falls back to loading from settings if not in env
- ✅ Sets the API key in environment for other processes
- ✅ Better error messages and debugging info
- ✅ Uses the proper indexing function from `index_kb.py`

### 2. Updated Docker Compose (`docker-compose.yml`)
- ✅ Added volume mount for `data/` directory (persists vector store)
- ✅ Increased healthcheck start period to 60s (allows time for indexing)
- ✅ Ensures `.env` file is loaded via `env_file`

### 3. Updated Dockerfile (`Dockerfile.api`)
- ✅ Added `.env.example` copy for reference

## How to Run

### 1. Ensure `.env` file exists in project root:

```env
LLM_API_KEY=sk-your-actual-api-key-here
RAG_MAX_DISTANCE=1.5
RAG_CONFIDENCE_MAX_DISTANCE=1.3
```

### 2. Build and run:

```bash
docker-compose down  # Stop any running containers
docker-compose build --no-cache  # Rebuild with fixes
docker-compose up  # Start services
```

### 3. What to Expect

**First startup:**
```
============================================================
Support Co-Pilot API - Starting Up
============================================================

✓ .env file found at /app/.env
✓ LLM_API_KEY found in environment (********sk-xy)
Vector store is empty or missing. Indexing knowledge base...
Clearing existing collection...
Indexing files...
  ✓ Eligibility_Documents/Kredila Education Loan Eligibility Checklist – India.pdf (45 chunks)
  ...
✓ Successfully indexed 1234 chunks
Starting uvicorn server...
```

**Subsequent startups:**
```
✓ Vector store exists (164.0 KB)
Using existing vector store.
Starting uvicorn server...
```

## Verification

### Check if API key is loaded:
```bash
docker-compose exec api python -c "from api.config import get_settings; print('API Key:', 'SET' if get_settings().llm_api_key else 'NOT SET')"
```

### Check vector store:
```bash
docker-compose exec api python -c "from tools.vector_store import VectorStore; s = VectorStore(); s._ensure_client(); print('Chunks:', s.count())"
```

### Test retrieval:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What'\''s the loan policy for a student in 12th and want to study abroad in science field.", "session_id": "test123"}'
```

## Troubleshooting

### Issue: "LLM_API_KEY not found"
**Solution:**
1. Verify `.env` file exists in project root (same directory as `docker-compose.yml`)
2. Check `.env` has `LLM_API_KEY=sk-...` (no quotes, no spaces around `=`)
3. Rebuild: `docker-compose build --no-cache`
4. Check logs: `docker-compose logs api | grep LLM_API_KEY`

### Issue: "SentenceTransformer fallback failed"
**Solution:**
- This means `LLM_API_KEY` is not being found
- Follow the steps above to ensure `.env` is properly loaded
- Or install sentence-transformers: `pip install sentence-transformers` (but OpenAI embeddings are better)

### Issue: Vector store not indexing
**Solution:**
1. Check logs: `docker-compose logs api`
2. Verify `data/kb/hackathon_dataset/` has files
3. Check API key is set: `docker-compose exec api env | grep LLM_API_KEY`
4. Manually index: `docker-compose exec api python scripts/index_kb.py --clear`

## Key Changes

1. **Entrypoint now explicitly handles API key**:
   - Checks environment variables first
   - Falls back to settings
   - Sets in environment for consistency

2. **Better error messages**:
   - Shows if API key is found
   - Shows last 4 chars for verification (masked)
   - Clear warnings if not found

3. **Proper indexing**:
   - Uses the same `index_directory` function as the standalone script
   - Handles errors gracefully
   - Shows progress

## Files Modified

- ✅ `scripts/docker_entrypoint.py` - Fixed API key loading
- ✅ `docker-compose.yml` - Added volume mount, increased start period
- ✅ `Dockerfile.api` - Added .env.example reference

The fix ensures that `LLM_API_KEY` from your `.env` file is properly loaded and passed to the vector store for embeddings!

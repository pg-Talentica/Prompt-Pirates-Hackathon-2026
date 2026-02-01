# Docker Compose Setup - Ready to Run!

## ✅ What I've Done

1. **Created Docker entrypoint script** (`scripts/docker_entrypoint.py`)
   - Automatically indexes knowledge base on first startup
   - Checks if vector store exists before indexing
   - Starts API server after indexing

2. **Updated Dockerfile.api**
   - Added entrypoint to handle indexing
   - Increased healthcheck start period to allow indexing time

3. **Created documentation**
   - `DOCKER_RUN.md` - Complete Docker instructions
   - This file - Quick setup guide

## 🚀 Quick Start Commands

### 1. Ensure .env file exists

Create `.env` file in project root with at minimum:

```env
LLM_API_KEY=your_openai_api_key_here
RAG_MAX_DISTANCE=1.5
RAG_CONFIDENCE_MAX_DISTANCE=1.3
```

### 2. Build and Start

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

### 3. What Happens

1. **API container starts**
2. **Entrypoint script runs**:
   - Checks if vector store exists
   - If empty, indexes `data/kb/hackathon_dataset/`
   - Starts uvicorn server
3. **UI container starts** (after API is healthy)
4. **Services available**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - UI: http://localhost

### 4. Test Your Query

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What'\''s the loan policy for a student in 12th and want to study abroad in science field.",
    "session_id": "test123"
  }'
```

## 🔄 Re-indexing

To force re-indexing:

```bash
# Stop services
docker-compose down

# Remove vector store
rm -rf data/vector_store/*

# Restart (will auto-index)
docker-compose up
```

Or manually in running container:

```bash
docker-compose exec api python scripts/index_kb.py --clear
```

## 📋 Useful Commands

```bash
# View logs
docker-compose logs -f api

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up
```

## ✅ Expected Behavior

After running `docker-compose up --build`:

1. **First time**:
   - Vector store is empty → indexing runs automatically
   - You'll see: "Indexing knowledge base..."
   - Then: "Starting uvicorn server..."
   - API becomes healthy after ~30-60 seconds

2. **Subsequent runs**:
   - Vector store exists → uses existing data
   - API starts immediately

3. **Your query should now work**:
   - Retrieval finds relevant chunks
   - Distance thresholds are lenient (1.5/1.3)
   - Query expansion helps with edge cases
   - Response is generated from retrieved context

## 🐛 Troubleshooting

### API not starting
- Check logs: `docker-compose logs api`
- Verify `.env` has `LLM_API_KEY`
- Check if port 8000 is available

### Indexing fails
- Check logs for errors
- Verify `data/kb/hackathon_dataset/` has files
- Ensure `LLM_API_KEY` is set (needed for embeddings)

### Port conflicts
- Edit `docker-compose.yml` to change ports
- API: `ports: - "8001:8000"`
- UI: `ports: - "8080:80"`

## 📝 Files Modified

- `Dockerfile.api` - Added entrypoint
- `scripts/docker_entrypoint.py` - Auto-indexing script
- `scripts/docker_entrypoint.sh` - Shell version (backup)

## 🎯 Next Steps

1. **Create `.env` file** with your `LLM_API_KEY`
2. **Run**: `docker-compose up --build`
3. **Wait** for indexing to complete (first time only)
4. **Test** with your query
5. **Enjoy** the fixed RAG system!

The fixes are all in place - just need to run docker-compose! 🚀

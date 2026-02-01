# Running with Docker Compose

## Quick Start

1. **Create `.env` file** (if not exists):
   ```bash
   cp .env.example .env
   # Edit .env and add your LLM_API_KEY
   ```

2. **Build and start services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the services**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - UI: http://localhost (port 80)

## What Happens on Startup

The API container will:
1. Check if vector store exists
2. If empty, automatically index the knowledge base from `data/kb/hackathon_dataset/`
3. Start the FastAPI server

## Re-indexing

To force re-indexing, you can:

**Option 1: Delete vector store and restart**
```bash
docker-compose down
rm -rf data/vector_store/*
docker-compose up
```

**Option 2: Run indexing manually in container**
```bash
docker-compose exec api python scripts/index_kb.py --clear
```

## Testing Your Query

Once services are running:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What'\''s the loan policy for a student in 12th and want to study abroad in science field.",
    "session_id": "test123"
  }'
```

## Useful Commands

**View logs:**
```bash
docker-compose logs -f api
```

**Restart services:**
```bash
docker-compose restart
```

**Stop services:**
```bash
docker-compose down
```

**Rebuild and restart:**
```bash
docker-compose up --build --force-recreate
```

## Troubleshooting

### Vector store not indexing
- Check logs: `docker-compose logs api`
- Verify `LLM_API_KEY` is set in `.env`
- Check if `data/kb/hackathon_dataset/` has files
- Ensure `pypdf` is installed (included in requirements.txt)

### API not starting
- Check health: `curl http://localhost:8000/health`
- View logs: `docker-compose logs api`
- Verify `.env` file exists and has `LLM_API_KEY`

### Port conflicts
- Change ports in `docker-compose.yml` if 8000 or 80 are in use
- Update API port: `ports: - "8001:8000"`
- Update UI port: `ports: - "8080:80"`

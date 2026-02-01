# Run Project - Quick Commands

Since dependencies need to be installed in your environment, here are the exact commands to run:

## 1. Install Dependencies

```bash
cd /Users/raghunandan/Documents/Prompt-Pirates-Hackathon-2026
pip install -r requirements.txt
```

## 2. Re-Index Knowledge Base

```bash
python scripts/index_kb.py --clear
```

## 3. Verify Setup

```bash
python scripts/verify_rag_setup.py
```

## 4. Test Retrieval

```bash
python scripts/diagnose_retrieval.py
```

## 5. Start API Server

```bash
uvicorn api.main:app --reload
```

## Or Run All at Once

```bash
python scripts/rerun_project.py
```

## Test Your Query

Once the server is running:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What'\''s the loan policy for a student in 12th and want to study abroad in science field.",
    "session_id": "test123"
  }'
```

## What to Expect

After re-indexing:
- Vector store will have chunks from all PDF and TXT files
- Retrieval should work with your query
- Distance thresholds are now more lenient (1.5/1.3)
- Query expansion will help with edge cases

The fixes are already in place - you just need to re-index the knowledge base!

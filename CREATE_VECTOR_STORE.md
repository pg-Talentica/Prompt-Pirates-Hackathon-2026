# Create Vector Store - Instructions

## Quick Method

Since dependencies need to be installed, here are the commands to create your vector store:

### Option 1: Using the Standalone Script

```bash
# Install dependencies first
pip install chromadb pypdf

# Or install all requirements
pip install -r requirements.txt

# Run the standalone script
python scripts/create_vector_store.py
```

### Option 2: Using the Original Script

```bash
# Install dependencies
pip install -r requirements.txt

# Run indexing
python scripts/index_kb.py --clear
```

### Option 3: Using Docker (Recommended)

```bash
# This will automatically index on first startup
docker-compose up --build
```

## What Gets Indexed

The script will index all files from:
- `data/kb/hackathon_dataset/`

Including:
- All `.txt` files (recursively)
- All `.pdf` files (recursively)

## Output

After indexing, you'll have:
- Vector store at: `data/vector_store/chroma.sqlite3`
- All document chunks embedded and searchable
- Ready for RAG retrieval

## Requirements

- `chromadb` - Vector database
- `pypdf` - PDF text extraction
- `openai` (optional but recommended) - Better embeddings if `LLM_API_KEY` is set

## Expected Output

```
============================================================
Creating Vector Store
============================================================

✓ LLM_API_KEY found

Knowledge base: data/kb/hackathon_dataset
Vector store: data/vector_store

Found 20 .txt files and 14 .pdf files

Creating vector store...
Clearing existing collection...
Indexing files...

[1/34] ✓ Eligibility_Documents/Kredila Education Loan Eligibility Checklist – India.pdf (45 chunks)
[2/34] ✓ Eligibility_Documents/Kredila Eligibility Checklist – Canada (International).pdf (52 chunks)
...

============================================================
Indexing Complete!
============================================================
✓ Indexed 34 files
✓ Created 1234 chunks
✓ Vector store now contains 1234 chunks
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'pydantic'"
**Solution**: Install dependencies: `pip install -r requirements.txt`

### "ModuleNotFoundError: No module named 'chromadb'"
**Solution**: `pip install chromadb`

### "ModuleNotFoundError: No module named 'pypdf'"
**Solution**: `pip install pypdf`

### PDF files not indexing
- Check if `pypdf` is installed
- Verify PDF files are readable
- Check logs for specific errors

### Empty vector store
- Verify `data/kb/hackathon_dataset/` has files
- Check if indexing completed successfully
- Review logs for errors

## After Creating Vector Store

Once the vector store is created, you can:

1. **Test retrieval**:
   ```bash
   python scripts/diagnose_retrieval.py
   ```

2. **Start API server**:
   ```bash
   uvicorn api.main:app --reload
   ```

3. **Or use Docker**:
   ```bash
   docker-compose up
   ```

The vector store will be automatically used by the RAG system for retrieval!

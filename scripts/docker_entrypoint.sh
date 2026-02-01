#!/bin/bash
# Docker entrypoint: Index KB if needed, then start API server

set -e

echo "=========================================="
echo "Support Co-Pilot API - Starting Up"
echo "=========================================="

# Check if vector store exists and has data
VECTOR_STORE="/app/data/vector_store"
KB_DIR="/app/data/kb/hackathon_dataset"

echo "Checking vector store..."
if [ ! -f "$VECTOR_STORE/chroma.sqlite3" ] || [ ! -s "$VECTOR_STORE/chroma.sqlite3" ]; then
    echo "Vector store is empty or missing. Indexing knowledge base..."
    python scripts/index_kb.py --kb-dir "$KB_DIR" --vector-dir "$VECTOR_STORE" || {
        echo "WARNING: Indexing failed. Continuing anyway..."
    }
else
    echo "Vector store exists. Checking if re-indexing is needed..."
    # Optionally check if KB files are newer than vector store
    # For now, we'll skip re-indexing if vector store exists
    echo "Using existing vector store."
fi

echo "Starting API server..."
exec "$@"

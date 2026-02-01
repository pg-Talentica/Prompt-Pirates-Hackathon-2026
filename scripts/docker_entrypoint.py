#!/usr/bin/env python3
"""Docker entrypoint: Index KB if needed, then start API server."""

import sys
import os
import subprocess
from pathlib import Path

# Project root on path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def check_and_index():
    """Check if vector store needs indexing."""
    vector_store = Path("/app/data/vector_store")
    kb_dir = Path("/app/data/kb/hackathon_dataset")
    
    print("=" * 60)
    print("Support Co-Pilot API - Starting Up")
    print("=" * 60)
    print()
    
    # Check for API key - prioritize environment variables
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    
    if api_key:
        print(f"✓ LLM_API_KEY found in environment ({'*' * 10}{api_key[-4:] if len(api_key) > 4 else ''})")
        # Ensure it's set in environment for other processes
        os.environ["LLM_API_KEY"] = api_key
    else:
        print("⚠ LLM_API_KEY not found in environment variables")
        print("  Attempting to load from settings...")
        try:
            from api.config import get_settings
            settings = get_settings()
            api_key = settings.llm_api_key
            if api_key and api_key.strip():
                print(f"✓ LLM_API_KEY loaded from settings ({'*' * 10}{api_key[-4:] if len(api_key) > 4 else ''})")
                # Set in environment for other processes
                os.environ["LLM_API_KEY"] = api_key
            else:
                print("⚠ LLM_API_KEY not set in .env file")
                print("  Will use fallback embeddings (sentence-transformers)")
                print("  For better results, set LLM_API_KEY in .env file")
                api_key = None
        except Exception as e:
            print(f"⚠ Could not load settings: {e}")
            print("  Will use fallback embeddings")
            api_key = None
    print()
    
    # Check if vector store exists and has data
    chroma_db = vector_store / "chroma.sqlite3"
    
    if not chroma_db.exists() or chroma_db.stat().st_size == 0:
        print("Vector store is empty or missing. Indexing knowledge base...")
        print()
        try:
            # Use the index_kb script which handles everything properly
            from scripts.index_kb import index_directory
            from tools.vector_store import VectorStore
            from data.chunking import DEFAULT_CHUNKING
            
            # Create vector store with explicit API key
            store = VectorStore(persist_directory=str(vector_store), api_key=api_key)
            
            # Clear existing collection
            print("Clearing existing collection...")
            store._ensure_client()
            try:
                store._client.delete_collection(store._collection_name)
                print("✓ Cleared existing collection")
            except Exception as e:
                print(f"  (No existing collection to clear: {e})")
            store._client = None
            store._collection = None
            
            # Recreate store after clearing
            store = VectorStore(persist_directory=str(vector_store), api_key=api_key)
            
            # Index all files
            print("Indexing files...")
            total = index_directory(kb_dir, store)
            
            print()
            print(f"✓ Successfully indexed {total} chunks")
            
        except Exception as e:
            print(f"✗ Indexing failed: {e}")
            import traceback
            traceback.print_exc()
            print()
            print("⚠ Continuing anyway - API will start but retrieval may not work")
            print("  You can manually index later or restart the container")
    else:
        size_kb = chroma_db.stat().st_size / 1024
        print(f"✓ Vector store exists ({size_kb:.1f} KB)")
        print("Using existing vector store.")
    
    print()


def main():
    """Entrypoint: check/index, then exec the command."""
    # Verify .env file exists (for debugging)
    env_file = Path("/app/.env")
    if env_file.exists():
        print(f"✓ .env file found at {env_file}")
    else:
        print(f"⚠ .env file not found at {env_file}")
        print("  Environment variables should be set via docker-compose env_file")
    print()
    
    check_and_index()
    
    # Execute the command passed to the container
    if len(sys.argv) > 1:
        cmd = sys.argv[1:]
        print(f"Starting: {' '.join(cmd)}")
        print("=" * 60)
        print()
        os.execvp(cmd[0], cmd)
    else:
        # Default: start uvicorn
        print("Starting uvicorn server...")
        print("=" * 60)
        print()
        os.execvp("uvicorn", [
            "uvicorn",
            "api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])


if __name__ == "__main__":
    main()

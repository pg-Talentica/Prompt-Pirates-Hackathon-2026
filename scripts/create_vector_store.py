#!/usr/bin/env python3
"""Standalone script to create vector store - minimal dependencies.

This script indexes the knowledge base without requiring all project imports.
Run: python scripts/create_vector_store.py
"""

import sys
import logging
from pathlib import Path

# Add project root to path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Create vector store by indexing knowledge base."""
    print("=" * 60)
    print("Creating Vector Store")
    print("=" * 60)
    print()
    
    # Check dependencies
    try:
        import chromadb
        import pypdf
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install chromadb pypdf")
        print("\nOr install all requirements:")
        print("  pip install -r requirements.txt")
        return 1
    
    # Check for OpenAI API key (optional but recommended)
    try:
        from api.config import get_settings
        settings = get_settings()
        api_key = settings.llm_api_key
        if not api_key:
            print("⚠ WARNING: LLM_API_KEY not set in .env")
            print("  Will use fallback embedding model (may be less accurate)")
            print("  Set LLM_API_KEY in .env for better embeddings")
            api_key = None
        else:
            print("✓ LLM_API_KEY found")
    except Exception as e:
        print(f"⚠ Could not load settings: {e}")
        print("  Will use fallback embedding model")
        api_key = None
    
    print()
    
    # Import after dependency check
    try:
        from tools.vector_store import VectorStore
        from data.chunking import DEFAULT_CHUNKING
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("  This script requires the project structure.")
        print("  Please install dependencies: pip install -r requirements.txt")
        return 1
    
    # Setup paths
    kb_dir = Path("data/kb/hackathon_dataset")
    vector_dir = Path("data/vector_store")
    
    if not kb_dir.exists():
        print(f"✗ Knowledge base directory not found: {kb_dir}")
        return 1
    
    print(f"Knowledge base: {kb_dir}")
    print(f"Vector store: {vector_dir}")
    print()
    
    # Count files
    txt_files = list(kb_dir.rglob("*.txt"))
    pdf_files = list(kb_dir.rglob("*.pdf"))
    total_files = len(txt_files) + len(pdf_files)
    
    print(f"Found {len(txt_files)} .txt files and {len(pdf_files)} .pdf files")
    print()
    
    if total_files == 0:
        print("✗ No files to index!")
        return 1
    
    # Create vector store
    print("Creating vector store...")
    store = VectorStore(persist_directory=vector_dir, api_key=api_key)
    
    # Clear existing collection
    print("Clearing existing collection...")
    try:
        store._ensure_client()
        try:
            store._client.delete_collection(store._collection_name)
            logger.info("Cleared existing collection")
        except Exception as e:
            logger.info("No existing collection to clear: %s", e)
        store._client = None
        store._collection = None
    except Exception as e:
        print(f"⚠ Warning during clear: {e}")
    
    # Index files
    print("Indexing files...")
    print()
    
    total_chunks = 0
    indexed_files = 0
    failed_files = []
    
    # Index all files
    all_files = sorted(list(txt_files) + list(pdf_files))
    
    for i, file_path in enumerate(all_files, 1):
        try:
            rel_path = file_path.relative_to(kb_dir)
            source_file = str(rel_path).replace("\\", "/")
            
            # Read file
            if file_path.suffix.lower() == ".txt":
                text = file_path.read_text(encoding="utf-8", errors="replace")
            elif file_path.suffix.lower() == ".pdf":
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                parts = []
                for page in reader.pages:
                    parts.append(page.extract_text() or "")
                text = "\n\n".join(parts)
            else:
                continue
            
            if not text.strip():
                logger.warning("Skip %s: empty", source_file)
                continue
            
            # Add to vector store
            chunks = store.add_document(source_file=source_file, text=text, config=DEFAULT_CHUNKING)
            total_chunks += chunks
            indexed_files += 1
            
            print(f"[{i}/{total_files}] ✓ {source_file} ({chunks} chunks)")
            
        except Exception as e:
            logger.error("Failed to index %s: %s", file_path.name, e)
            failed_files.append((file_path.name, str(e)))
            print(f"[{i}/{total_files}] ✗ {file_path.name}: {e}")
    
    print()
    print("=" * 60)
    print("Indexing Complete!")
    print("=" * 60)
    print(f"✓ Indexed {indexed_files} files")
    print(f"✓ Created {total_chunks} chunks")
    
    if failed_files:
        print(f"⚠ {len(failed_files)} files failed:")
        for name, error in failed_files:
            print(f"  - {name}: {error}")
    
    # Verify
    store._ensure_client()
    count = store.count()
    print(f"✓ Vector store now contains {count} chunks")
    print()
    print("Vector store location: data/vector_store/")
    print()
    
    return 0 if not failed_files else 1


if __name__ == "__main__":
    raise SystemExit(main())

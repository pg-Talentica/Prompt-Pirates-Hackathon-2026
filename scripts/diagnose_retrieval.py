#!/usr/bin/env python3
"""Diagnose RAG retrieval issues - test query and check vector store status."""

import sys
from pathlib import Path

# Project root on path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from tools.retrieval import retrieve
from tools.vector_store import VectorStore
from api.config import get_settings


def main() -> int:
    print("=" * 80)
    print("RAG Retrieval Diagnostic Tool")
    print("=" * 80)
    
    # Check vector store
    print("\n1. Checking Vector Store Status...")
    try:
        store = VectorStore()
        store._ensure_client()
        count = store.count()
        print(f"   ✓ Total chunks in vector store: {count}")
        if count == 0:
            print("   ✗ ERROR: Vector store is empty! Run: python scripts/index_kb.py")
            return 1
    except Exception as e:
        print(f"   ✗ ERROR accessing vector store: {e}")
        return 1
    
    # Check settings
    print("\n2. Checking RAG Configuration...")
    try:
        settings = get_settings()
        print(f"   rag_max_distance: {settings.rag_max_distance}")
        print(f"   rag_confidence_max_distance: {settings.rag_confidence_max_distance}")
        print(f"   LLM API Key configured: {'Yes' if settings.llm_api_key else 'No'}")
    except Exception as e:
        print(f"   ⚠ Warning: Could not load settings: {e}")
    
    # Test query
    test_query = "What's the loan policy for a student in 12th and want to study abroad in science field."
    print(f"\n3. Testing Retrieval with Query:")
    print(f"   Query: {test_query}")
    print()
    
    try:
        results = retrieve(query=test_query, k=8)
        print(f"   Retrieved {len(results)} results")
        
        if not results:
            print("   ✗ ERROR: No results returned!")
            print("   Possible causes:")
            print("   - Vector store is empty (run: python scripts/index_kb.py)")
            print("   - All results filtered out by distance threshold")
            print("   - Query embedding failed")
            return 1
        
        print("\n   Top Results:")
        for i, r in enumerate(results[:5], 1):
            source = r.get("source_file", "?")
            distance = r.get("distance")
            text = (r.get("text", "") or "")[:300].replace("\n", " ")
            if len((r.get("text") or "")) > 300:
                text += "..."
            
            print(f"\n   [{i}] Source: {source}")
            if distance is not None:
                print(f"       Distance: {distance:.4f} {'✓' if distance <= 1.1 else '✗ (too high)'}")
            else:
                print(f"       Distance: None")
            print(f"       Text: {text}")
        
        # Check if results pass thresholds
        distances = [r.get("distance") for r in results if r.get("distance") is not None]
        if distances:
            best_distance = min(distances)
            conf_threshold = get_settings().rag_confidence_max_distance
            print(f"\n   Best distance: {best_distance:.4f}")
            print(f"   Confidence threshold: {conf_threshold}")
            if best_distance > conf_threshold:
                print(f"   ✗ WARNING: Best distance {best_distance:.4f} > {conf_threshold}")
                print(f"   This will cause 'out of context' response!")
                print(f"   Consider:")
                print(f"   - Increasing rag_confidence_max_distance in .env")
                print(f"   - Re-indexing with better chunking strategy")
                print(f"   - Checking if query matches document content")
            else:
                print(f"   ✓ Best distance is within threshold")
        else:
            print("\n   ⚠ No distance values available")
            
    except Exception as e:
        print(f"   ✗ ERROR during retrieval: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 80)
    print("Diagnostic complete!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

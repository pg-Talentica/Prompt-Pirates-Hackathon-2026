#!/usr/bin/env python3
"""Verify RAG setup: check vector store, test retrieval, and provide diagnostics.

This script helps diagnose RAG issues by:
1. Checking if vector store has data
2. Testing retrieval with sample queries
3. Providing recommendations for fixes
"""

import sys
from pathlib import Path

# Project root on path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from tools.vector_store import VectorStore
from tools.retrieval import retrieve
from api.config import get_settings


def check_vector_store() -> tuple[bool, int, str]:
    """Check if vector store exists and has data."""
    try:
        store = VectorStore()
        store._ensure_client()
        count = store.count()
        if count == 0:
            return False, 0, "Vector store is empty. Run: python scripts/index_kb.py"
        return True, count, f"Vector store has {count} chunks"
    except Exception as e:
        return False, 0, f"Error accessing vector store: {e}"


def test_retrieval(query: str) -> tuple[bool, list, str]:
    """Test retrieval with a query."""
    try:
        results = retrieve(query=query, k=5)
        if not results:
            return False, [], "No results returned"
        
        distances = [r.get("distance") for r in results if r.get("distance") is not None]
        if distances:
            best_distance = min(distances)
            conf_threshold = get_settings().rag_confidence_max_distance
            if best_distance > conf_threshold:
                return True, results, f"Results found but best distance {best_distance:.4f} > threshold {conf_threshold}"
            return True, results, f"Retrieval successful: {len(results)} results, best distance {best_distance:.4f}"
        return True, results, f"Retrieval successful: {len(results)} results (no distance values)"
    except Exception as e:
        return False, [], f"Retrieval error: {e}"


def main() -> int:
    print("=" * 80)
    print("RAG Setup Verification")
    print("=" * 80)
    
    # Check vector store
    print("\n1. Checking Vector Store...")
    has_data, count, message = check_vector_store()
    status = "✓" if has_data else "✗"
    print(f"   {status} {message}")
    
    if not has_data:
        print("\n   ACTION REQUIRED:")
        print("   1. Ensure you have documents in data/kb/hackathon_dataset/")
        print("   2. Run: python scripts/index_kb.py --clear")
        print("   3. Verify PDF files are readable (requires pypdf: pip install pypdf)")
        return 1
    
    # Check settings
    print("\n2. Checking RAG Configuration...")
    try:
        settings = get_settings()
        print(f"   ✓ rag_max_distance: {settings.rag_max_distance}")
        print(f"   ✓ rag_confidence_max_distance: {settings.rag_confidence_max_distance}")
        print(f"   ✓ LLM API Key: {'Configured' if settings.llm_api_key else 'NOT CONFIGURED'}")
        if not settings.llm_api_key:
            print("   ⚠ WARNING: LLM_API_KEY not set. Embeddings may use fallback model.")
    except Exception as e:
        print(f"   ✗ Error loading settings: {e}")
    
    # Test queries
    print("\n3. Testing Retrieval...")
    test_queries = [
        "What's the loan policy for a student in 12th and want to study abroad in science field.",
        "education loan eligibility for international studies",
        "loan policy for students studying abroad",
        "eligibility requirements for education loans",
    ]
    
    all_passed = True
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Test {i}: {query[:60]}...")
        success, results, message = test_retrieval(query)
        status = "✓" if success else "✗"
        print(f"   {status} {message}")
        
        if results:
            print(f"      Top sources:")
            for j, r in enumerate(results[:3], 1):
                source = r.get("source_file", "?")
                distance = r.get("distance")
                dist_str = f" (distance: {distance:.4f})" if distance is not None else ""
                print(f"        {j}. {source}{dist_str}")
        
        if not success or (results and not any(r.get("distance", 999) <= get_settings().rag_confidence_max_distance 
                                               for r in results if r.get("distance") is not None)):
            all_passed = False
    
    # Recommendations
    print("\n4. Recommendations...")
    if all_passed:
        print("   ✓ RAG setup looks good!")
    else:
        print("   ⚠ Issues detected. Recommendations:")
        print("   1. Re-index the knowledge base: python scripts/index_kb.py --clear")
        print("   2. Check if PDF files are being indexed (requires pypdf)")
        print("   3. Verify LLM_API_KEY is set for better embeddings")
        print("   4. Consider adjusting rag_confidence_max_distance in .env if thresholds are too strict")
        print("   5. Check logs for detailed retrieval information")
    
    print("\n" + "=" * 80)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

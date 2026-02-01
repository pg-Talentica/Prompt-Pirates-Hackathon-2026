#!/usr/bin/env python3
"""Re-run project: Re-index knowledge base and verify RAG setup.

This script:
1. Checks/installs dependencies
2. Re-indexes the knowledge base
3. Verifies RAG setup
4. Tests retrieval with user query
"""

import sys
import subprocess
from pathlib import Path

# Project root on path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Step 1: Checking dependencies...")
    try:
        import pydantic
        import chromadb
        import openai
        import pypdf
        print("✓ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False


def reindex_kb():
    """Re-index the knowledge base."""
    print("\nStep 2: Re-indexing knowledge base...")
    try:
        from scripts.index_kb import main as index_main
        result = index_main()
        if result == 0:
            print("✓ Knowledge base re-indexed successfully")
            return True
        else:
            print("✗ Re-indexing failed")
            return False
    except Exception as e:
        print(f"✗ Error during re-indexing: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_setup():
    """Verify RAG setup."""
    print("\nStep 3: Verifying RAG setup...")
    try:
        from scripts.verify_rag_setup import main as verify_main
        result = verify_main()
        return result == 0
    except Exception as e:
        print(f"✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieval():
    """Test retrieval with user query."""
    print("\nStep 4: Testing retrieval with user query...")
    try:
        from scripts.diagnose_retrieval import main as diagnose_main
        result = diagnose_main()
        return result == 0
    except Exception as e:
        print(f"✗ Error during retrieval test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution."""
    print("=" * 60)
    print("Re-running Project - RAG Setup")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("Error: Please run this script from the project root directory")
        return 1
    
    success = True
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n⚠ Please install dependencies first:")
        print("   pip install -r requirements.txt")
        print("\nContinuing anyway...")
    
    # Step 2: Re-index
    if not reindex_kb():
        success = False
    
    # Step 3: Verify
    if not verify_setup():
        success = False
    
    # Step 4: Test
    if not test_retrieval():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Re-run complete! All checks passed.")
    else:
        print("⚠ Re-run complete with some issues. Review output above.")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Start the API server:")
    print("   uvicorn api.main:app --reload")
    print()
    print("2. Or test via API:")
    print('   curl -X POST http://localhost:8000/api/chat \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "What'\''s the loan policy for a student in 12th and want to study abroad in science field.", "session_id": "test123"}\'')
    print()
    
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

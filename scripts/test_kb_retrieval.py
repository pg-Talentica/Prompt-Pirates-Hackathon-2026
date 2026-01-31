#!/usr/bin/env python3
"""Verify that the KB dataset is indexed and retrieval returns data from data/kb/.

Run: python scripts/test_kb_retrieval.py

This proves the RAG flow reads from your dataset.
"""

import sys
from pathlib import Path

# Project root on path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from tools.retrieval import retrieve


def main() -> int:
    print("=" * 60)
    print("KB Retrieval Test – Proving data is read from data/kb/")
    print("=" * 60)

    # Query that matches content in the sample KB
    # (runbook_003.txt has "diagnose --env prod"; product_004.txt has "Export", "100 MB payload")
    queries = [
        "What diagnostic command should I run for high latency alerts?",
        "What is the Export feature and where is it in the Dashboard?",
        "Payment Service database failover resolution",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i}: {query} ---\n")
        results = retrieve(query=query, k=3)
        if not results:
            print("  [No results – KB may be empty. Run: python scripts/index_kb.py]")
            continue
        for j, r in enumerate(results, 1):
            source = r.get("source_file", "?")
            text = (r.get("text", "") or "")[:200].replace("\n", " ")
            if len((r.get("text") or "")) > 200:
                text += "..."
            print(f"  [{j}] source_file: {source}")
            print(f"      text: {text}")
            print()
    print("=" * 60)
    print("If you see source_file values (e.g. runbook_003.txt, product_004.txt),")
    print("the data IS being read from data/kb/.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

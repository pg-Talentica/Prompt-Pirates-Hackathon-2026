#!/usr/bin/env python3
"""Run QA Validation Agent - Standalone script.

This script runs the QA Agent independently without interfering with the main system.
Usage:
    python scripts/run_qa_validation.py [--test-cases PATH] [--output-dir PATH] [--use-api] [--api-url URL]
"""

import sys
from pathlib import Path

# Add project root to path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agents.qa_validation import main

if __name__ == "__main__":
    main()

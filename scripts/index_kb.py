#!/usr/bin/env python3
"""Index the knowledge-base corpus into the vector store.

Reads .txt (and optionally .pdf) files from data/kb/, chunks them using
data.chunking, embeds with OpenAI (or sentence-transformers fallback),
and persists to Chroma at data/vector_store.

Run after generating the corpus (scripts/generate_corpus.py) and before
using retrieval. Usage:

    python scripts/index_kb.py [--kb-dir DATA/KB] [--vector-dir DATA/VECTOR_STORE]
"""

import argparse
import logging
import sys
from pathlib import Path

# Project root on path for api.config and tools
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent.parent
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from data.chunking import DEFAULT_CHUNKING
from tools.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _read_text(path: Path) -> str:
    """Read file as UTF-8 text."""
    return path.read_text(encoding="utf-8", errors="replace")


def _read_pdf(path: Path) -> str:
    """Extract text from PDF (requires pypdf or similar)."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("Install pypdf to index PDFs: pip install pypdf") from None
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n\n".join(parts)


def index_directory(
    kb_dir: Path,
    vector_store: VectorStore,
    extensions: tuple[str, ...] = (".txt", ".pdf"),
    recursive: bool = True,
) -> int:
    """Index all supported files under kb_dir (recursively). Returns total chunks added."""
    total = 0
    if recursive:
        files = [f for f in kb_dir.rglob("*") if f.is_file() and f.suffix.lower() in extensions]
    else:
        files = [f for f in kb_dir.iterdir() if f.is_file() and f.suffix.lower() in extensions]
    if not files:
        logger.warning("No %s files in %s", extensions, kb_dir)
        return 0
    for path in sorted(files):
        try:
            if path.suffix.lower() == ".txt":
                text = _read_text(path)
            elif path.suffix.lower() == ".pdf":
                text = _read_pdf(path)
            else:
                continue
        except Exception as e:
            logger.warning("Skip %s: %s", path.name, e)
            continue
        if not text.strip():
            logger.warning("Skip %s: empty", path.name)
            continue
        # Use path relative to kb_dir for source_file (e.g. Eligibility_Documents/doc.pdf)
        rel_path = path.relative_to(kb_dir)
        source_file = str(rel_path).replace("\\", "/")
        n = vector_store.add_document(source_file=source_file, text=text, config=DEFAULT_CHUNKING)
        total += n
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Index KB corpus into vector store")
    parser.add_argument("--kb-dir", type=Path, default=Path("data/kb/hackathon_dataset"), help="Knowledge-base directory (default: hackathon_dataset)")
    parser.add_argument("--vector-dir", type=Path, default=Path("data/vector_store"), help="Chroma persist directory")
    parser.add_argument("--api-key", type=str, default=None, help="OpenAI API key (default: LLM_API_KEY from env)")
    parser.add_argument("--clear", action="store_true", help="Clear existing collection before indexing (start fresh)")
    args = parser.parse_args()

    if not args.kb_dir.is_dir():
        logger.error("KB directory not found: %s", args.kb_dir)
        return 1

    api_key = args.api_key
    if not api_key:
        try:
            from api.config import get_settings
            api_key = get_settings().llm_api_key or None
        except Exception:
            api_key = None

    store = VectorStore(persist_directory=args.vector_dir, api_key=api_key)
    if args.clear:
        store._ensure_client()
        try:
            store._client.delete_collection(store._collection_name)
            logger.info("Cleared collection %s", store._collection_name)
        except Exception as e:
            logger.warning("Clear collection failed (may not exist): %s", e)
        store._client = None
        store._collection = None
    total = index_directory(args.kb_dir, store)
    logger.info("Indexed %d chunks from %s into %s", total, args.kb_dir, args.vector_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

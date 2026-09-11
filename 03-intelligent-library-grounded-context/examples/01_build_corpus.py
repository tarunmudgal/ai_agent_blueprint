"""01 — Build the corpus: chunk four documents, embed once.

Demonstrates:
  * chunk_text() splitting each of the chapter's four fixtures on
    blank-line paragraph breaks
  * Corpus.build() embedding every chunk exactly once, with
    task_type="RETRIEVAL_DOCUMENT" and each chunk's source document name as
    `title`
  * that building the index is a one-time cost paid before any question is
    ever asked - every later example in this chapter re-runs this same
    build step, then searches it repeatedly

What to look for in the output:
  1. Chunk counts differ per document because paragraph count differs -
     this is the entire "chunking algorithm" for this chapter, and it is
     honestly this simple.
  2. Each chunk's preview is a plain string prefix - nothing structural is
     lost by chunking, it is just a smaller unit to search over.
  3. This script never asks a question. It only proves the index exists.
     02_ops_library_qa.py is where retrieval actually gets used.

Run:  python3 examples/01_build_corpus.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    Corpus,
    banner,
    chunk_text,
    doc_api_rate_limits,
    doc_onboarding_faq,
    doc_refund_policy,
    document_text,
    get_client,
    rule,
    truncate,
)

# The four documents that make up this chapter's small library, paired with
# the name each will be cited under. Order does not affect retrieval - the
# similarity search in Corpus.search() considers every chunk regardless of
# which document it came from.
LIBRARY: list[tuple[str, str]] = [
    ("document_text", document_text),
    ("doc_refund_policy", doc_refund_policy),
    ("doc_onboarding_faq", doc_onboarding_faq),
    ("doc_api_rate_limits", doc_api_rate_limits),
]


def build_corpus() -> Corpus:
    """Chunk all four fixtures into one flat list of Chunks (not yet embedded)."""
    chunks = []
    for doc_name, text in LIBRARY:
        chunks.extend(chunk_text(text, doc_name))
    return Corpus(chunks)


def main() -> None:
    client = get_client()

    banner("Chunking the four-document library")
    corpus = build_corpus()
    counts: dict[str, int] = {}
    for chunk in corpus.chunks:
        counts[chunk.doc_name] = counts.get(chunk.doc_name, 0) + 1
    for doc_name, _ in LIBRARY:
        print(f"  {doc_name}: {counts.get(doc_name, 0)} chunk(s)")
    print(f"  total: {len(corpus.chunks)} chunk(s) across {len(LIBRARY)} documents")

    rule()
    banner("Embedding every chunk once (task_type=RETRIEVAL_DOCUMENT)")
    corpus.build(client)
    print(f"embedded {len(corpus.chunks)} chunks with model=EMBED_MODEL")

    rule()
    banner("Chunk preview")
    for chunk in corpus.chunks:
        dims = len(chunk.vector) if chunk.vector is not None else 0
        print(f"[{chunk.label}] ({dims} dims)")
        print(f"  {truncate(chunk.text, limit=160)}")

    rule()
    print(
        "Index built. This is a plain Python list of Chunks held in memory - "
        "a teaching-scale stand-in for a real vector database or Google's "
        "own managed File Search API, not a production recommendation."
    )


if __name__ == "__main__":
    main()

"""06 — A golden-set eval harness for retrieval.

Mirrors Chapter 2's examples/05_pipeline_eval.py: a small golden set of
(query, expected_doc_name) pairs, run each through the REAL Corpus.search(),
and grade whether the top result's source document matches expectation. No
simulated payloads - every case goes through the real embed_content calls,
same as Chapter 2's eval ran the real classify + route stages.

Demonstrates:
  * a golden set spanning all four documents, including the deliberate
    lexical-overlap trap (a "charged twice" query that must resolve to
    doc_refund_policy, not document_text)
  * a per-case pass/fail table and an overall precision figure, in the same
    table style as Chapter 2's eval

What to look for in the output:
  1. A FAIL row means retrieval put a chunk from the wrong document on
     top - read the query and decide whether the golden label, the corpus,
     or MIN_SIMILARITY-style tuning needs to change.
  2. Eight cases is a smoke test, exactly as Chapter 2 said about its own
     golden set - extend it before trusting this number on a larger corpus.

Run:  python3 examples/06_retrieval_eval.py
"""
import sys
from dataclasses import dataclass
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
)

PASS_THRESHOLD = 0.75

# (query, expected_doc_name)
GOLDEN_CASES: list[tuple[str, str]] = [
    ("How many customers were charged twice in the October incident?",
     "document_text"),
    ("If a customer says they were charged twice, are they automatically "
     "owed a refund?", "doc_refund_policy"),
    ("How long do confirmed duplicate-charge refunds take to process?",
     "doc_refund_policy"),
    ("What caused the payment gateway degradation on 3 October?",
     "document_text"),
    ("How do I reset my account password?", "doc_onboarding_faq"),
    ("Can one login be used across multiple team workspaces?",
     "doc_onboarding_faq"),
    ("Are API rate limits counted per key or per project?",
     "doc_api_rate_limits"),
    ("Does a 429 response count toward token usage for billing?",
     "doc_api_rate_limits"),
]


def build_corpus() -> Corpus:
    chunks = []
    for doc_name, text in [
        ("document_text", document_text),
        ("doc_refund_policy", doc_refund_policy),
        ("doc_onboarding_faq", doc_onboarding_faq),
        ("doc_api_rate_limits", doc_api_rate_limits),
    ]:
        chunks.extend(chunk_text(text, doc_name))
    return Corpus(chunks)


@dataclass
class CaseResult:
    index: int
    query: str
    expected_doc: str
    actual_doc: str
    top_score: float
    passed: bool


def run_case(corpus: Corpus, client, index: int, query: str, expected_doc: str) -> CaseResult:
    chunk, score = corpus.search(client, query, k=1)[0]
    return CaseResult(
        index=index,
        query=query,
        expected_doc=expected_doc,
        actual_doc=chunk.doc_name,
        top_score=score,
        passed=(chunk.doc_name == expected_doc),
    )


def print_table(results: list[CaseResult]) -> None:
    header = f"{'#':<3}{'':<6}{'expected':<20}{'actual':<20}{'score'}"
    print(header)
    print("-" * 74)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"{r.index:<3}{status:<6}{r.expected_doc:<20}{r.actual_doc:<20}"
              f"{r.top_score:.3f}")


def main() -> None:
    client = get_client()

    banner("Building the corpus")
    corpus = build_corpus()
    corpus.build(client)

    banner(f"Golden-set retrieval eval: {len(GOLDEN_CASES)} cases")
    results = []
    for index, (query, expected_doc) in enumerate(GOLDEN_CASES, start=1):
        result = run_case(corpus, client, index, query, expected_doc)
        results.append(result)
        print(f"  ran case {index}/{len(GOLDEN_CASES)}")

    banner("Per-case results")
    print_table(results)

    passed = sum(1 for r in results if r.passed)
    precision = passed / len(results) if results else 0.0

    rule()
    print(f"precision@1: {passed}/{len(results)} = {precision:.1%}   "
          f"threshold: {PASS_THRESHOLD:.0%}")

    banner("Result")
    if precision < PASS_THRESHOLD:
        print("BELOW THRESHOLD - exiting non-zero so CI blocks the merge.")
        sys.exit(1)
    print("At or above threshold.")


if __name__ == "__main__":
    main()
